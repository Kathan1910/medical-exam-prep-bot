# core/agents/question_generator.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Dict, Any
from .nodes import QuestionGeneratorNodes
from config import settings
from utils.logger import setup_logger
import asyncio

logger = setup_logger(__name__)

class QuestionState(TypedDict):
    """State schema for the question generation workflow"""
    chapter_id: int
    difficulty: str
    include_images: bool
    retrieved_chunks: List[Dict[str, Any]]
    retrieved_images: List[Dict[str, Any]]
    image_analysis: Optional[Dict[str, Any]]
    question_draft: Optional[Dict[str, Any]]
    validation_result: Optional[Dict[str, Any]]
    final_question: Optional[Dict[str, Any]]
    generation_attempt: int
    uniqueness_check: Optional[Dict[str, Any]]
    error: Optional[str]

class QuestionGeneratorAgent:
    """LangGraph-based agent for question generation with validation"""
    
    def __init__(self):
        self.nodes = QuestionGeneratorNodes()
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        workflow = StateGraph(QuestionState)
        
        # Add nodes
        workflow.add_node("retrieve_context", self.nodes.retrieve_context)
        workflow.add_node("generate_question", self.nodes.generate_question)
        workflow.add_node("validate_accuracy", self.nodes.validate_accuracy)
        workflow.add_node("add_citations", self.nodes.add_citations)
        
        # Define flow
        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "generate_question")
        workflow.add_edge("generate_question", "validate_accuracy")
        
        # Conditional edge: regenerate if validation fails
        workflow.add_conditional_edges(
            "validate_accuracy",
            self._should_regenerate,
            {
                "regenerate": "generate_question",
                "continue": "add_citations",
                "fail": END
            }
        )
        
        workflow.add_edge("add_citations", END)
        
        return workflow.compile()
    
    def _should_regenerate(self, state: QuestionState) -> str:
        """
        Decision function for validation routing
        
        Returns:
            - "regenerate": Try generating again
            - "continue": Validation passed, continue to citations
            - "fail": Max attempts reached, stop
        """
        validation = state.get('validation_result')
        attempt = state.get('generation_attempt', 1)
        
        if not validation:
            return "fail"
        
        # Check if max attempts reached
        if attempt >= settings.MAX_REGENERATION_ATTEMPTS:
            logger.warning(f"Max regeneration attempts ({attempt}) reached")
            return "fail" if not validation['is_valid'] else "continue"
        
        # Check validation criteria
        is_valid = validation.get('is_valid', False)
        confidence = validation.get('confidence_score', 0)
        medical_accuracy = validation.get('medical_accuracy', True)
        
        if not medical_accuracy:
            logger.warning("Medical accuracy check failed, regenerating")
            return "regenerate"
        
        if not is_valid or confidence < settings.VALIDATION_CONFIDENCE_THRESHOLD:
            logger.info(f"Validation failed (confidence: {confidence}), regenerating")
            return "regenerate"
        
        logger.info("Validation passed")
        return "continue"
    
    async def generate_single_question(
        self,
        chapter_id: int,
        difficulty: str = "intermediate",
        include_images: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a single validated question
        
        Args:
            chapter_id: ID of the chapter
            difficulty: Question difficulty level
            include_images: Whether to include image-based questions
            
        Returns:
            Generated question or None if failed
        """
        initial_state: QuestionState = {
            'chapter_id': chapter_id,
            'difficulty': difficulty,
            'include_images': include_images,
            'retrieved_chunks': [],
            'retrieved_images': [],
            'image_analysis': None,
            'question_draft': None,
            'validation_result': None,
            'final_question': None,
            'generation_attempt': 0,
            'uniqueness_check': None,
            'error': None
        }
        
        try:
            logger.info(f"Starting question generation for chapter {chapter_id}")
            final_state = await self.graph.ainvoke(initial_state)
            
            if final_state.get('error'):
                logger.error(f"Generation failed: {final_state['error']}")
                return None
            
            if not final_state.get('final_question'):
                logger.error("No question generated")
                return None
            
            return final_state['final_question']
            
        except Exception as e:
            logger.error(f"Error in question generation workflow: {e}", exc_info=True)
            return None
    
    async def generate_batch_questions(
        self,
        chapter_id: int,
        count: int,
        difficulty: str = "intermediate",
        include_images: bool = False,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple questions concurrently in batches
        
        Args:
            chapter_id: ID of the chapter
            count: Number of questions to generate
            difficulty: Question difficulty level
            include_images: Whether to include image-based questions
            max_concurrent: Number of questions to generate simultaneously
            
        Returns:
            List of generated questions
        """
        questions = []
        
        logger.info(f"Starting batch generation: {count} questions, {max_concurrent} concurrent")
        
        # Process in batches of max_concurrent
        for i in range(0, count, max_concurrent):
            batch_size = min(max_concurrent, count - i)
            
            logger.info(f"Generating batch {i//max_concurrent + 1}: {batch_size} questions")
            
            # Create tasks for this batch
            tasks = [
                self.generate_single_question(chapter_id, difficulty, include_images)
                for _ in range(batch_size)
            ]
            
            # Run concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out failures and exceptions
            valid_questions = [
                q for q in batch_results 
                if isinstance(q, dict) and q is not None
            ]
            
            questions.extend(valid_questions)
            
            logger.info(f"Batch complete: {len(valid_questions)}/{batch_size} successful")
        
        logger.info(f"Batch generation complete: {len(questions)}/{count} questions generated")
        
        return questions