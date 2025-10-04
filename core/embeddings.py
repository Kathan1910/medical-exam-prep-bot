# core/embeddings.py
from openai import AsyncOpenAI
from typing import List
import asyncio
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class EmbeddingManager:
    """Manage OpenAI embeddings"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed single text"""
        try:
            response = await self.client.embeddings.create(
                input=text,
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            raise
    
    async def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts in batches"""
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                response = await self.client.embeddings.create(
                    input=batch,
                    model=self.model
                )
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)
                
                logger.info(f"Embedded batch {i//self.batch_size + 1}/{(len(texts)-1)//self.batch_size + 1}")
                
            except Exception as e:
                logger.error(f"Error in batch {i//self.batch_size}: {e}")
                raise
        
        return all_embeddings