# utils/session_init.py
import streamlit as st
from storage.json_store import JSONStorage
from config import settings

def init_session_state():
    """Initialize session state - call this at the start of EVERY page"""
    
    # Storage initialization
    if 'storage' not in st.session_state:
        st.session_state.storage = JSONStorage(settings.CACHE_PATH)
    
    # Navigation state
    if 'current_question_idx' not in st.session_state:
        st.session_state.current_question_idx = 0
    
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    
    if 'answered_questions' not in st.session_state:
        st.session_state.answered_questions = set()
    
    if 'current_score' not in st.session_state:
        st.session_state.current_score = 0
    
    # RAG chat state
    if 'rag_messages' not in st.session_state:
        st.session_state.rag_messages = []
    
    if 'selected_rag_chapter' not in st.session_state:
        st.session_state.selected_rag_chapter = None
    
    # Initialize empty JSON files if they don't exist
    storage = st.session_state.storage
    for filename in ['chapters', 'questions', 'attempts', 'images', 'rag_conversations']:
        file_path = settings.CACHE_PATH / f"{filename}.json"
        if not file_path.exists():
            storage.save(filename, [])