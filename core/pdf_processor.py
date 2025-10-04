# core/pdf_processor.py
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
import io
from typing import List, Dict, Tuple
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PDFProcessor:
    """Process PDF files to extract text and images"""
    
    def __init__(self):
        self.images_path = settings.IMAGES_PATH
        self.images_path.mkdir(parents=True, exist_ok=True)
    
    def process_pdf(
        self, 
        pdf_path: Path, 
        chapter_id: int
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Extract text chunks and images from PDF
        
        Returns:
            Tuple of (text_chunks, images)
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        chunks = []
        images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text with structure
            text_dict = page.get_text("dict")
            blocks = text_dict["blocks"]
            
            # Process text blocks
            page_text = ""
            for block in blocks:
                if block["type"] == 0:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            page_text += span["text"] + " "
                    page_text += "\n"
            
            # Create chunks from page text
            page_chunks = self._chunk_text(page_text, page_num + 1, chapter_id)
            chunks.extend(page_chunks)
            
            # Extract images
            image_list = page.get_images()
            for img_idx, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    
                    # Save image
                    image_filename = f"ch{chapter_id}_p{page_num+1}_img{img_idx}.png"
                    image_path = self.images_path / image_filename
                    
                    image_bytes = base_image["image"]
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    pil_image.save(image_path)
                    
                    images.append({
                        'chapter_id': chapter_id,
                        'page_number': page_num + 1,
                        'filename': image_filename,
                        'path': str(image_path),
                        'width': base_image["width"],
                        'height': base_image["height"]
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting image on page {page_num + 1}: {e}")
        
        doc.close()
        
        logger.info(f"Extracted {len(chunks)} chunks and {len(images)} images")
        return chunks, images
    
    def _chunk_text(
        self, 
        text: str, 
        page_number: int, 
        chapter_id: int
    ) -> List[Dict]:
        """
        Split text into chunks with overlap
        """
        chunks = []
        
        # Simple paragraph-based chunking
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        current_chunk = ""
        for para in paragraphs:
            if len(para) < settings.MIN_CHUNK_LENGTH:
                continue
            
            if len(current_chunk) + len(para) < settings.CHUNK_SIZE:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        'chapter_id': chapter_id,
                        'page_number': page_number,
                        'text': current_chunk.strip(),
                        'chunk_index': len(chunks)
                    })
                current_chunk = para + "\n\n"
        
        # Add last chunk
        if current_chunk:
            chunks.append({
                'chapter_id': chapter_id,
                'page_number': page_number,
                'text': current_chunk.strip(),
                'chunk_index': len(chunks)
            })
        
        return chunks