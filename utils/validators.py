# utils/validators.py
from typing import Dict, Any, List
import re

def validate_question_structure(question: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate question structure
    
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    # Required fields
    required_fields = ['question', 'options', 'correct_answer', 'explanation']
    for field in required_fields:
        if field not in question:
            errors.append(f"Missing required field: {field}")
    
    # Options validation
    if 'options' in question:
        if not isinstance(question['options'], dict):
            errors.append("Options must be a dictionary")
        elif len(question['options']) != 4:
            errors.append("Must have exactly 4 options (A, B, C, D)")
        elif set(question['options'].keys()) != {'A', 'B', 'C', 'D'}:
            errors.append("Options must be labeled A, B, C, D")
    
    # Correct answer validation
    if 'correct_answer' in question:
        if question['correct_answer'] not in ['A', 'B', 'C', 'D']:
            errors.append("Correct answer must be A, B, C, or D")
    
    return len(errors) == 0, errors