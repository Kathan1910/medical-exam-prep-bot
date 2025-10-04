# utils/cascade_delete.py
from pathlib import Path
from typing import Dict, Any
from storage.json_store import JSONStorage
from storage.vector_store import LocalVectorStore
from config import settings
from utils.logger import setup_logger
import os

logger = setup_logger(__name__)

def cascade_delete_chapter(chapter_id: int, storage: JSONStorage) -> Dict[str, Any]:
    """
    Delete a chapter and all related data
    
    Returns:
        Dictionary with deletion statistics
    """
    stats = {
        'chapter_deleted': False,
        'pdf_deleted': False,
        'questions_deleted': 0,
        'attempts_deleted': 0,
        'images_deleted': 0,
        'rag_conversations_deleted': 0,
        'embeddings_deleted': 0,
        'errors': []
    }
    
    try:
        # 1. Get chapter info
        chapters = storage.load('chapters')
        chapter = next((c for c in chapters if c['id'] == chapter_id), None)
        
        if not chapter:
            stats['errors'].append(f"Chapter {chapter_id} not found")
            return stats
        
        logger.info(f"Starting cascade delete for chapter {chapter_id}: {chapter.get('name')}")
        
        # 2. Delete PDF file
        if 'pdf_path' in chapter:
            pdf_path = Path(chapter['pdf_path'])
            if pdf_path.exists():
                try:
                    os.remove(pdf_path)
                    stats['pdf_deleted'] = True
                    logger.info(f"Deleted PDF: {pdf_path}")
                except Exception as e:
                    stats['errors'].append(f"Failed to delete PDF: {e}")
        
        # 3. Delete questions
        questions = storage.load('questions')
        questions_to_keep = [q for q in questions if q.get('chapter_id') != chapter_id]
        stats['questions_deleted'] = len(questions) - len(questions_to_keep)
        storage.save('questions', questions_to_keep)
        logger.info(f"Deleted {stats['questions_deleted']} questions")
        
        # 4. Delete attempts (only for deleted questions)
        deleted_question_ids = [q['id'] for q in questions if q.get('chapter_id') == chapter_id]
        attempts = storage.load('attempts')
        attempts_to_keep = [a for a in attempts if a.get('question_id') not in deleted_question_ids]
        stats['attempts_deleted'] = len(attempts) - len(attempts_to_keep)
        storage.save('attempts', attempts_to_keep)
        logger.info(f"Deleted {stats['attempts_deleted']} attempts")
        
        # 5. Delete images
        images = storage.load('images')
        chapter_images = [img for img in images if img.get('chapter_id') == chapter_id]
        
        # Delete image files
        for img in chapter_images:
            if 'path' in img:
                img_path = Path(img['path'])
                if img_path.exists():
                    try:
                        os.remove(img_path)
                        stats['images_deleted'] += 1
                    except Exception as e:
                        stats['errors'].append(f"Failed to delete image {img_path}: {e}")
        
        # Remove from storage
        images_to_keep = [img for img in images if img.get('chapter_id') != chapter_id]
        storage.save('images', images_to_keep)
        logger.info(f"Deleted {stats['images_deleted']} images")
        
        # 6. Delete RAG conversations
        rag_conversations = storage.load('rag_conversations')
        rag_to_keep = [conv for conv in rag_conversations if conv.get('chapter_id') != chapter_id]
        stats['rag_conversations_deleted'] = len(rag_conversations) - len(rag_to_keep)
        storage.save('rag_conversations', rag_to_keep)
        logger.info(f"Deleted {stats['rag_conversations_deleted']} RAG conversations")
        
        # 7. Delete embeddings from vector store
        try:
            vector_store = LocalVectorStore()
            vector_store.load(settings.EMBEDDINGS_PATH)
            
            # Filter out embeddings for this chapter
            filtered_metadata = [
                meta for meta in vector_store.metadata 
                if meta.get('chapter_id') != chapter_id
            ]
            
            stats['embeddings_deleted'] = len(vector_store.metadata) - len(filtered_metadata)
            
            if stats['embeddings_deleted'] > 0:
                # Rebuild vector store without this chapter's embeddings
                # This requires rebuilding the entire FAISS index
                logger.warning("Vector store rebuild required - embeddings marked for deletion")
                # Note: Full rebuild would need re-embedding remaining chapters
                # For now, just update metadata
                vector_store.metadata = filtered_metadata
                vector_store.save(settings.EMBEDDINGS_PATH)
            
            logger.info(f"Removed {stats['embeddings_deleted']} embeddings from vector store")
            
        except Exception as e:
            stats['errors'].append(f"Failed to delete embeddings: {e}")
        
        # 8. Delete chapter entry
        chapters_to_keep = [c for c in chapters if c['id'] != chapter_id]
        storage.save('chapters', chapters_to_keep)
        stats['chapter_deleted'] = True
        logger.info(f"Deleted chapter {chapter_id} entry")
        
        logger.info(f"Cascade delete completed for chapter {chapter_id}")
        
    except Exception as e:
        logger.error(f"Error during cascade delete: {e}", exc_info=True)
        stats['errors'].append(f"Cascade delete failed: {e}")
    
    return stats