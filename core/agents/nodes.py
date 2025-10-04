# core/agents/nodes.py
from typing import Dict, Any, List
from openai import AsyncOpenAI
import json
from config import settings
from storage.vector_store import LocalVectorStore
from core.embeddings import EmbeddingManager
from core.image_processor import ImageProcessor
from storage.json_store import JSONStorage
from .prompts import get_generation_prompt, get_validation_prompt
from utils.logger import setup_logger
import difflib

logger = setup_logger(__name__)

class QuestionGeneratorNodes:
    """Individual nodes for the LangGraph workflow"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_manager = EmbeddingManager()
        self.image_processor = ImageProcessor()
        self.vector_store = LocalVectorStore()
        self.vector_store.load(settings.EMBEDDINGS_PATH)
        self.storage = JSONStorage(settings.CACHE_PATH)
    
    def _calculate_question_similarity(self, q1: str, q2: str) -> float:
        """Calculate similarity between two questions using SequenceMatcher"""
        return difflib.SequenceMatcher(None, q1.lower(), q2.lower()).ratio()
    
    def _is_question_unique(self, new_question: str, chapter_id: int, threshold: float = 0.7) -> tuple[bool, str]:
        """
        Check if question is unique compared to existing questions
        
        Returns:
            (is_unique, reason)
        """
        existing_questions = self.storage.filter('questions', chapter_id=chapter_id)
        
        for existing_q in existing_questions:
            existing_text = existing_q.get('question', '')
            similarity = self._calculate_question_similarity(new_question, existing_text)
            
            if similarity > threshold:
                return False, f"Question is {similarity*100:.1f}% similar to existing question: '{existing_text[:80]}...'"
        
        return True, "Question is unique"
    
    async def retrieve_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 1: Retrieve relevant context from vector store
        """
        logger.info(f"Retrieving context for chapter {state['chapter_id']}")
        
        # Get existing questions to avoid similar content retrieval
        existing_questions = self.storage.filter('questions', chapter_id=state['chapter_id'])
        
        # Create query based on difficulty with uniqueness consideration
        query_map = {
            "intermediate": f"fundamental concepts and definitions from chapter {state['chapter_id']}",
            "advanced": f"clinical applications and mechanisms from chapter {state['chapter_id']}",
            "complex": f"complex cases and differential diagnosis from chapter {state['chapter_id']}"
        }
        
        query = query_map.get(state['difficulty'], query_map['intermediate'])
        
        # Get embedding
        query_embedding = await self.embedding_manager.embed_text(query)
        
        # Search vector store - retrieve more results for diversity
        results = self.vector_store.search(
            query_embedding,
            k=10,  # Increased from 5 for more variety
            filter_chapter=state['chapter_id']
        )
        
        # Filter out chunks that were used in recent questions
        if existing_questions:
            used_chunk_indices = set()
            for q in existing_questions[-5:]:  # Check last 5 questions
                used_chunk_indices.update(q.get('source_chunks', []))
            
            # Prioritize unused chunks
            unused_results = [r for r in results if r['metadata'].get('chunk_index') not in used_chunk_indices]
            
            if len(unused_results) >= 5:
                results = unused_results[:5]
            else:
                # Mix unused and used chunks
                results = unused_results + [r for r in results if r['metadata'].get('chunk_index') in used_chunk_indices][:5-len(unused_results)]
        else:
            results = results[:5]
        
        state['retrieved_chunks'] = results
        
        # Retrieve images if requested
        if state.get('include_images', False):
            images = self.storage.filter('images', chapter_id=state['chapter_id'])
            if images:
                import random
                selected_images = random.sample(images, min(2, len(images)))
                state['retrieved_images'] = selected_images
            else:
                state['retrieved_images'] = []
        
        logger.info(f"Retrieved {len(results)} chunks and {len(state.get('retrieved_images', []))} images")
        
        return state
    
    async def generate_question(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 2: Generate question using GPT-4o
        """
        logger.info("Generating question")
        
        # Prepare context
        context_text = "\n\n".join([
            f"[Page {chunk['metadata']['page_number']}]\n{chunk['metadata']['text'][:500]}"
            for chunk in state['retrieved_chunks'][:3]
        ])
        
        # Analyze image if present
        image_context = ""
        if state.get('retrieved_images'):
            image = state['retrieved_images'][0]
            
            surrounding_text = next(
                (chunk['metadata']['text'] for chunk in state['retrieved_chunks']
                 if chunk['metadata']['page_number'] == image['page_number']),
                ""
            )
            
            analysis = await self.image_processor.analyze_image(
                image['path'],
                surrounding_text[:500]
            )
            image_context = analysis['analysis']
            state['image_analysis'] = analysis
        
        # Generate prompt
        prompt = get_generation_prompt(
            state['difficulty'],
            context_text,
            image_context
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a medical education expert creating unique, high-quality exam questions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=settings.TEMPERATURE
            )
            
            question_draft = json.loads(response.choices[0].message.content)
            
            # Check uniqueness
            is_unique, reason = self._is_question_unique(
                question_draft['question'],
                state['chapter_id']
            )
            
            if not is_unique:
                logger.warning(f"Question not unique: {reason}")
                state['uniqueness_check'] = {
                    'is_unique': False,
                    'reason': reason
                }
            else:
                state['uniqueness_check'] = {
                    'is_unique': True,
                    'reason': reason
                }
            
            # Format explanation properly
            if isinstance(question_draft.get('explanation'), dict):
                # New format - combine all parts into a comprehensive text with dynamic headers
                exp = question_draft['explanation']
                correct_option = question_draft['options'][question_draft['correct_answer']]
                
                formatted_explanation = f"""
**Why "{correct_option}" is the correct answer:**
{exp.get('correct_reasoning', '')}

**Analysis of Other Options:**
{chr(10).join([f"- Option {k} ({question_draft['options'][k]}): {v}" for k, v in exp.get('distractor_analysis', {}).items() if k != question_draft['correct_answer']])}

**Clinical Context:**
{exp.get('clinical_context', '')}

**Key Takeaway:**
{exp.get('key_takeaway', '')}
"""
                question_draft['explanation'] = formatted_explanation.strip()
            
            # Format references with quotes
            if 'references' in question_draft:
                citations = []
                for ref in question_draft['references']:
                    if isinstance(ref, dict):
                        citation = f"Page {ref.get('page', 'N/A')}"
                        if ref.get('section'):
                            citation += f", {ref['section']}"
                        if ref.get('quote'):
                            citation += f": \"{ref['quote'][:100]}...\""
                        citations.append(citation)
                    else:
                        citations.append(str(ref))
                question_draft['citations'] = citations
            
            # Add metadata
            question_draft['chapter_id'] = state['chapter_id']
            question_draft['difficulty'] = state['difficulty']
            if state.get('retrieved_images'):
                question_draft['image_path'] = state['retrieved_images'][0]['path']
            
            state['question_draft'] = question_draft
            state['generation_attempt'] = state.get('generation_attempt', 0) + 1
            
            logger.info("Question generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            state['error'] = str(e)
        
        return state
    
    async def validate_accuracy(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 3: Validate medical accuracy, quality, and uniqueness
        """
        logger.info("Validating question")
        
        question_draft = state['question_draft']
        
        # Check uniqueness first
        if not state.get('uniqueness_check', {}).get('is_unique', True):
            logger.warning("Question failed uniqueness check")
            state['validation_result'] = {
                'is_valid': False,
                'confidence_score': 0,
                'issues': [state['uniqueness_check']['reason']],
                'medical_accuracy': True
            }
            return state
        
        # Prepare source context
        source_context = "\n".join([
            chunk['metadata']['text'][:300]
            for chunk in state['retrieved_chunks'][:2]
        ])
        
        # Validation prompt
        prompt = get_validation_prompt(question_draft, source_context)
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            validation = json.loads(response.choices[0].message.content)
            state['validation_result'] = validation
            
            logger.info(f"Validation complete: {validation['is_valid']}, confidence: {validation['confidence_score']}")
            
        except Exception as e:
            logger.error(f"Error validating question: {e}")
            state['validation_result'] = {
                'is_valid': False,
                'confidence_score': 0,
                'issues': [str(e)]
            }
        
        return state
    
    async def add_citations(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 4: Format with proper citations (already done in generation)
        """
        logger.info("Finalizing question with citations")
        
        question = state['question_draft']
        
        # Citations are already formatted in generate_question
        # Just add source chunk metadata
        question['source_chunks'] = [
            chunk['metadata']['chunk_index'] 
            for chunk in state['retrieved_chunks'][:3]
        ]
        
        # Add validation metadata
        if 'validation_result' in state:
            question['confidence_score'] = state['validation_result']['confidence_score']
        
        state['final_question'] = question
        
        logger.info("Question finalized successfully")
        
        return state