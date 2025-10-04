# core/image_processor.py
from openai import AsyncOpenAI
import base64
from pathlib import Path
from typing import Dict
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ImageProcessor:
    """Process and analyze medical images using GPT-4V"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def analyze_image(
        self, 
        image_path: str, 
        context: str = ""
    ) -> Dict[str, str]:
        """
        Analyze medical image with GPT-4V
        
        Args:
            image_path: Path to image file
            context: Optional surrounding text context
            
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Analyzing image: {image_path}")
        
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        prompt = f"""Analyze this medical image in detail. 

Context from textbook: {context if context else 'No additional context provided'}

Provide a comprehensive analysis including:
1. **Anatomical Structures**: Identify all visible anatomical structures
2. **Pathological Findings**: Note any abnormalities or pathology
3. **Clinical Significance**: Explain the diagnostic or educational value
4. **Key Features**: Highlight important features for learning
5. **Labels/Annotations**: Describe any visible labels or markings

Be precise and use medical terminology appropriate for exam preparation."""
        
        try:
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }],
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            
            logger.info("Image analysis completed successfully")
            
            return {
                'analysis': analysis,
                'model_used': settings.LLM_MODEL
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            raise