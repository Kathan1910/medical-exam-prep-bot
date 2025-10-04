# core/agents/nodes.py
from typing import Dict, Any, List
from openai import AsyncOpenAI
import json
import time
import random
from collections import Counter
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
        
        # Add caches for performance
        self._question_cache = {}  # chapter_id -> questions
        self._cache_timestamp = {}  # chapter_id -> timestamp
    
    def _get_cached_questions(self, chapter_id: int) -> list:
        """Get questions with caching to reduce disk I/O"""
        current_time = time.time()
        
        # Cache for 30 seconds
        if (chapter_id in self._question_cache and 
            current_time - self._cache_timestamp.get(chapter_id, 0) < 30):
            return self._question_cache[chapter_id]
        
        # Reload from disk
        questions = self.storage.filter('questions', chapter_id=chapter_id)
        self._question_cache[chapter_id] = questions
        self._cache_timestamp[chapter_id] = current_time
        
        return questions
    
    def _calculate_question_similarity(self, q1: str, q2: str) -> float:
        """Calculate similarity between two questions using SequenceMatcher"""
        return difflib.SequenceMatcher(None, q1.lower(), q2.lower()).ratio()
    
    def _extract_medical_terms(self, text: str) -> list[str]:
        """Extract key medical terms (capitalized words, >4 chars)"""
        words = text.split()
        return [w.lower() for w in words if len(w) > 4 and (w[0].isupper() or w.isupper())]
    
    def _is_question_unique(
        self, 
        new_question: str, 
        chapter_id: int, 
        threshold: float = 0.55  # Stricter than before (was 0.7)
    ) -> tuple[bool, str]:
        """
        Check if question is unique with both text similarity and semantic checks
        
        Returns:
            (is_unique, reason)
        """
        existing_questions = self._get_cached_questions(chapter_id)
        
        for existing_q in existing_questions:
            existing_text = existing_q.get('question', '')
            
            # Text similarity check
            text_similarity = self._calculate_question_similarity(new_question, existing_text)
            
            if text_similarity > threshold:
                return False, f"Text similarity {text_similarity*100:.1f}% exceeds threshold ({threshold*100:.0f}%)"
            
            # Additional check: compare key medical terms
            new_terms = set(self._extract_medical_terms(new_question))
            existing_terms = set(self._extract_medical_terms(existing_text))
            
            if new_terms and existing_terms:
                term_overlap = len(new_terms & existing_terms) / len(new_terms | existing_terms)
                if term_overlap > 0.7:  # 70% term overlap
                    return False, f"Medical term overlap {term_overlap*100:.1f}% too high"
        
        return True, "Question is unique"
    
    def _extract_covered_topics(self, questions: list) -> list[str]:
        """Extract main topics from existing questions"""
        topics = []
        for q in questions[-15:]:  # Last 15 questions
            # Extract key medical terms
            terms = self._extract_medical_terms(q.get('question', ''))
            topics.extend(terms)
        
        # Return most common topics
        return [topic for topic, _ in Counter(topics).most_common(10)]
    
    def _update_chunk_quality_scores(self, chunks: list, score: int):
        """Track which chunks produce high-quality questions"""
        try:
            quality_data = self.storage.load('chunk_quality') or {}
            
            for chunk in chunks[:3]:
                chunk_id = str(chunk['metadata']['chunk_index'])
                if chunk_id not in quality_data:
                    quality_data[chunk_id] = {'scores': [], 'avg': 0}
                
                quality_data[chunk_id]['scores'].append(score)
                # Keep only last 10 scores
                quality_data[chunk_id]['scores'] = quality_data[chunk_id]['scores'][-10:]
                quality_data[chunk_id]['avg'] = sum(quality_data[chunk_id]['scores']) / len(quality_data[chunk_id]['scores'])
            
            self.storage.save('chunk_quality', quality_data)
        except Exception as e:
            logger.warning(f"Failed to update chunk quality: {e}")
    
    async def retrieve_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 1: Retrieve relevant context from vector store with smart selection
        """
        logger.info(f"Retrieving context for chapter {state['chapter_id']}, difficulty: {state['difficulty']}")
        
        # Difficulty-based configuration
        context_config = {
            "intermediate": {"k": 15, "chunks_to_use": 3},  # Simpler, fewer chunks
            "advanced": {"k": 20, "chunks_to_use": 5},      # Standard
            "complex": {"k": 25, "chunks_to_use": 7}        # More context for complex
        }
        
        config = context_config.get(state['difficulty'], context_config['advanced'])
        
        # Get existing questions with cache
        existing_questions = self._get_cached_questions(state['chapter_id'])
        
        # Analyze what topics have been covered
        covered_topics = self._extract_covered_topics(existing_questions)
        
        # Build smarter query that avoids covered topics
        query_map = {
            "intermediate": f"fundamental concepts, definitions, basic mechanisms in medical textbook",
            "advanced": f"clinical applications, pathophysiology, diagnostic approach in medical context",
            "complex": f"complex cases, differential diagnosis, complications, multi-system integration"
        }
        
        base_query = query_map.get(state['difficulty'], query_map['intermediate'])
        
        # Add topic avoidance if we have covered topics
        if covered_topics:
            query = f"{base_query}. Focus on areas different from: {', '.join(covered_topics[:5])}"
        else:
            query = base_query
        
        # Get embedding
        query_embedding = await self.embedding_manager.embed_text(query)
        
        # Search vector store with expanded retrieval
        results = self.vector_store.search(
            query_embedding,
            k=config['k'],
            filter_chapter=state['chapter_id']
        )
        
        # Smart chunk selection with uniqueness and quality
        if existing_questions:
            used_chunk_indices = set()
            # Check last 20 questions instead of 5 for better diversity
            for q in existing_questions[-20:]:
                used_chunk_indices.update(q.get('source_chunks', []))
            
            # Separate unused and used chunks
            unused_results = [r for r in results if r['metadata'].get('chunk_index') not in used_chunk_indices]
            used_results = [r for r in results if r['metadata'].get('chunk_index') in used_chunk_indices]
            
            # Prioritize unused chunks with randomization
            if len(unused_results) >= config['chunks_to_use']:
                random.shuffle(unused_results)
                selected_results = unused_results[:config['chunks_to_use']]
            else:
                # Mix unused and high-quality used chunks
                random.shuffle(unused_results)
                random.shuffle(used_results)
                combined = unused_results + used_results
                selected_results = combined[:config['chunks_to_use']]
        else:
            # First questions - just randomize for variety
            random.shuffle(results)
            selected_results = results[:config['chunks_to_use']]
        
        state['retrieved_chunks'] = selected_results
        
        # Retrieve images if requested
        if state.get('include_images', False):
            images = self.storage.filter('images', chapter_id=state['chapter_id'])
            if images:
                selected_images = random.sample(images, min(2, len(images)))
                state['retrieved_images'] = selected_images
            else:
                state['retrieved_images'] = []
        
        logger.info(f"Retrieved {len(selected_results)} chunks and {len(state.get('retrieved_images', []))} images")
        
        return state
    
    async def generate_question(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 2: Generate question using GPT-4o with enhanced context
        """
        logger.info("Generating question")
        
        # Prepare context with appropriate amount based on difficulty
        chunks_to_use = len(state['retrieved_chunks'])
        context_text = "\n\n".join([
            f"[Source {i+1} - Page {chunk['metadata']['page_number']}]\n{chunk['metadata']['text'][:600]}"
            for i, chunk in enumerate(state['retrieved_chunks'])
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
                    {"role": "system", "content": "You are a medical education expert creating unique, high-quality exam questions. Focus on creating diverse questions that test different aspects of the material."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=settings.TEMPERATURE
            )
            
            question_draft = json.loads(response.choices[0].message.content)
            
            # Check uniqueness with enhanced method
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
            
            logger.info(f"Question generated successfully (attempt {state['generation_attempt']})")
            
        except Exception as e:
            logger.error(f"Error generating question: {e}", exc_info=True)
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
            
            logger.info(f"Validation complete: valid={validation['is_valid']}, confidence={validation['confidence_score']}")
            
        except Exception as e:
            logger.error(f"Error validating question: {e}", exc_info=True)
            state['validation_result'] = {
                'is_valid': False,
                'confidence_score': 0,
                'issues': [str(e)],
                'medical_accuracy': False
            }
        
        return state
    
    async def add_citations(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 4: Format with proper citations and quality tracking
        """
        logger.info("Finalizing question with citations")
        
        question = state['question_draft']
        
        # Add source chunk metadata
        question['source_chunks'] = [
            chunk['metadata']['chunk_index'] 
            for chunk in state['retrieved_chunks']
        ]
        
        # Add validation metadata
        if 'validation_result' in state:
            confidence = state['validation_result']['confidence_score']
            question['confidence_score'] = confidence
            
            # Update chunk quality scores for future prioritization
            self._update_chunk_quality_scores(
                state['retrieved_chunks'],
                confidence
            )
        
        state['final_question'] = question
        
        logger.info("Question finalized successfully")
        
        return state