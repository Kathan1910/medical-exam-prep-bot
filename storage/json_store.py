# storage/json_store.py
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)

class JSONStorage:
    """Thread-safe JSON storage manager"""
    
    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
    def _get_file_path(self, filename: str) -> Path:
        """Get full path for a JSON file"""
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        return self.cache_path / filename
    
    def load(self, filename: str) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        file_path = self._get_file_path(filename)
        
        if not file_path.exists():
            logger.info(f"File {filename} does not exist, returning empty list")
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} records from {filename}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {filename}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return []
    
    def save(self, filename: str, data: List[Dict[str, Any]]) -> bool:
        """Save data to JSON file"""
        file_path = self._get_file_path(filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Saved {len(data)} records to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")
            return False
    
    def append(self, filename: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Append item to JSON file"""
        data = self.load(filename)
        
        # Add metadata
        item['id'] = len(data) + 1
        item['created_at'] = datetime.now().isoformat()
        
        data.append(item)
        self.save(filename, data)
        
        logger.info(f"Appended item with id {item['id']} to {filename}")
        return item
    
    def update(self, filename: str, item_id: int, updates: Dict[str, Any]) -> bool:
        """Update an existing item"""
        data = self.load(filename)
        
        for item in data:
            if item.get('id') == item_id:
                item.update(updates)
                item['updated_at'] = datetime.now().isoformat()
                self.save(filename, data)
                logger.info(f"Updated item {item_id} in {filename}")
                return True
        
        logger.warning(f"Item {item_id} not found in {filename}")
        return False
    
    def get_by_id(self, filename: str, item_id: int) -> Optional[Dict[str, Any]]:
        """Get item by ID"""
        data = self.load(filename)
        return next((item for item in data if item.get('id') == item_id), None)
    
    def filter(self, filename: str, **filters) -> List[Dict[str, Any]]:
        """Filter items by criteria"""
        data = self.load(filename)
        
        result = data
        for key, value in filters.items():
            result = [item for item in result if item.get(key) == value]
        
        return result