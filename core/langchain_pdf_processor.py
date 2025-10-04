from typing import List, Dict
from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class LangchainPDFProcessor:
    """Process PDF files using Langchain's PyMuPDFLoader"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
        )
    
    def process_pdf(
        self, 
        pdf_path: Path,
        chapter_id: int
    ) -> List[Dict]:
        """
        Extract text from PDF using Langchain's PyMuPDFLoader
        
        Args:
            pdf_path: Path to the PDF file
            chapter_id: ID of the chapter
            
        Returns:
            List of text chunks with metadata
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            # Load PDF using Langchain's loader
            loader = PyMuPDFLoader(str(pdf_path))
            documents = loader.load()
            
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Format chunks with metadata
            formatted_chunks = []
            for i, chunk in enumerate(chunks):
                formatted_chunks.append({
                    'chapter_id': chapter_id,
                    'page_number': chunk.metadata.get('page', 0) + 1,  # Langchain uses 0-based pages
                    'text': chunk.page_content,
                    'chunk_index': i,
                    'source_file': str(pdf_path),
                    'start_index': chunk.metadata.get('start_index', 0)
                })
            
            logger.info(f"Extracted {len(formatted_chunks)} chunks from PDF")
            return formatted_chunks
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise
