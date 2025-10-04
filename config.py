# config.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    LLM_MODEL: str = "gpt-4o"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    
    # Storage
    BASE_PATH: Path = Path(__file__).parent
    DATA_PATH: Path = BASE_PATH / "storage" / "data"
    CACHE_PATH: Path = DATA_PATH / "cache"
    CHAPTERS_PATH: Path = DATA_PATH / "chapters"
    EMBEDDINGS_PATH: Path = DATA_PATH / "embeddings"
    
    # Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    EMBEDDING_BATCH_SIZE: int = 100
    
    # Langchain Settings
    TEXT_SPLITTER_TYPE: str = "recursive"  # Options: recursive, markdown, character
    LANGUAGE: str = "en"  # For potential future language handling
    
    # Question Generation
    VALIDATION_CONFIDENCE_THRESHOLD: int = 80
    MAX_REGENERATION_ATTEMPTS: int = 2
    
    class Config:
        env_file = ".env"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories
        for path in [self.DATA_PATH, self.CACHE_PATH, self.CHAPTERS_PATH, 
                     self.EMBEDDINGS_PATH]:
            path.mkdir(parents=True, exist_ok=True)

settings = Settings()