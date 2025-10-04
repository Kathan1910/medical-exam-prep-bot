# pages/5_🔍_Test_RAG.py
import streamlit as st
import asyncio
from storage.vector_store import LocalVectorStore
from core.embeddings import EmbeddingManager
from openai import AsyncOpenAI
from config import settings
from utils.logger import setup_logger
from utils.session_init import init_session_state
from utils.design_system import get_global_css, COLORS
from datetime import datetime

logger = setup_logger(__name__)

st.set_page_config(page_title="RAG Q&A", page_icon="🔍", layout="wide")
init_session_state()

# Apply global CSS
st.markdown(get_global_css(), unsafe_allow_html=True)

# Additional chat-specific CSS
st.markdown(f"""
<style>
    /* Chat container */
    .chat-container {{
        max-width: 900px;
        margin: 0 auto;
    }}
    
    /* User message */
    .user-message {{
        background: {COLORS['gradient_primary']};
        color: white;
        padding: 1rem 1.25rem;
        border-radius: 1.25rem 1.25rem 0.25rem 1.25rem;
        margin: 0.5rem 0;
        margin-left: auto;
        max-width: 80%;
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
    }}
    
    /* Assistant message */
    .assistant-message {{
        background: {COLORS['bg_primary']};
        border: 1px solid {COLORS['border']};
        padding: 1rem 1.25rem;
        border-radius: 1.25rem 1.25rem 1.25rem 0.25rem;
        margin: 0.5rem 0;
        margin-right: auto;
        max-width: 80%;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }}
    
    /* Chat input */
    .stChatInput {{
        border-radius: 1.5rem;
        border: 2px solid {COLORS['border']};
    }}
    
    .stChatInput:focus-within {{
        border-color: {COLORS['primary']};
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }}
</style>
""", unsafe_allow_html=True)

storage = st.session_state.storage
chapters = storage.load('chapters')

if not chapters:
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_secondary']};
        border: 2px dashed {COLORS['border']};
        border-radius: 1rem;
        padding: 3rem;
        text-align: center;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📚</div>
        <h2 style="color: {COLORS['text_primary']};">No chapters available</h2>
        <p style="color: {COLORS['text_secondary']};">Upload a chapter PDF first to start asking questions</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Initialize vector store and OpenAI client
vector_store = LocalVectorStore()
vector_store.load(settings.EMBEDDINGS_PATH)
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Initialize session state
if 'rag_messages' not in st.session_state:
    st.session_state.rag_messages = []
if 'selected_rag_chapter' not in st.session_state:
    st.session_state.selected_rag_chapter = chapters[0]['name'] if chapters else None
    
    if chapters:
        chapter_id = chapters[0]['id']
        previous_conversations = storage.filter('rag_conversations', chapter_id=chapter_id)
        
        for conv in previous_conversations[-10:]:
            st.session_state.rag_messages.append({
                "role": "user",
                "content": conv['user_message'],
                "timestamp": conv.get('created_at', '')
            })
            st.session_state.rag_messages.append({
                "role": "assistant",
                "content": conv['assistant_message'],
                "timestamp": conv.get('created_at', '')
            })

# Sidebar
with st.sidebar:
    
    st.markdown("### Settings")
    
    selected_chapter = st.selectbox(
        "Chapter",
        options=[c['name'] for c in chapters],
        index=0,
        key='chapter_selector'
    )
    
    # Update selected chapter
    if selected_chapter != st.session_state.selected_rag_chapter:
        st.session_state.selected_rag_chapter = selected_chapter
        
        chapter = next(c for c in chapters if c['name'] == selected_chapter)
        chapter_id = chapter['id']
        
        previous_conversations = storage.filter('rag_conversations', chapter_id=chapter_id)
        
        st.session_state.rag_messages = []
        for conv in previous_conversations[-10:]:
            st.session_state.rag_messages.append({
                "role": "user",
                "content": conv['user_message'],
                "timestamp": conv.get('created_at', '')
            })
            st.session_state.rag_messages.append({
                "role": "assistant",
                "content": conv['assistant_message'],
                "timestamp": conv.get('created_at', '')
            })
        
        st.rerun()
    
    st.divider()
    
    num_chunks = st.slider(
        "Context chunks",
        min_value=3,
        max_value=10,
        value=5,
        help="Number of text chunks to retrieve"
    )
    
    temperature = st.slider(
        "Creativity",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        help="Lower = more factual"
    )
    
    st.divider()
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.rag_messages = []
        st.rerun()
    
    if st.session_state.rag_messages:
        msg_count = len([m for m in st.session_state.rag_messages if m['role'] == 'user'])
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_tertiary']};
            padding: 0.75rem;
            border-radius: 0.5rem;
            text-align: center;
        ">
            <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem;">Messages</div>
            <div style="color: {COLORS['primary']}; font-size: 1.5rem; font-weight: 700;">{msg_count}</div>
        </div>
        """, unsafe_allow_html=True)

# Main chat area
st.markdown(f"""
<div style="
    background: {COLORS['gradient_primary']};
    padding: 1.5rem 2rem;
    border-radius: 1rem;
    margin-bottom: 1.5rem;
">
    <h1 style="color: white; margin: 0;">Ask Questions About: {st.session_state.selected_rag_chapter}</h1>
    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
        Get AI-powered answers from your textbook content
    </p>
</div>
""", unsafe_allow_html=True)

# Function to generate RAG answer
async def generate_rag_answer(question: str, chapter_id: int, num_chunks: int, temperature: float):
    """Generate answer using RAG approach"""
    
    embedding_manager = EmbeddingManager()
    query_embedding = await embedding_manager.embed_text(question)
    
    search_results = vector_store.search(
        query_embedding,
        k=num_chunks,
        filter_chapter=chapter_id
    )
    
    if not search_results:
        return "I couldn't find any relevant information in this chapter to answer your question. Try rephrasing or asking about a different topic.", []
    
    context_parts = []
    for i, result in enumerate(search_results, 1):
        chunk = result['metadata']
        context_parts.append(
            f"[Source {i} - Page {chunk['page_number']}]\n{chunk['text']}"
        )
    
    combined_context = "\n\n".join(context_parts)
    
    system_prompt = """You are a medical education assistant. Provide clear, accurate answers based on the textbook content provided.

Guidelines:
- Answer directly and comprehensively
- Cite sources naturally (e.g., "According to page 45..." or "As mentioned in the text...")
- Use appropriate medical terminology
- If the context doesn't fully answer the question, mention what information is available
- Keep answers focused and educational"""

    user_prompt = f"""Question: {question}

Context from textbook:
{combined_context}

Provide a clear, comprehensive answer based on this context."""

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=1500
    )
    
    answer = response.choices[0].message.content
    
    return answer, search_results

# Display chat messages
chat_container = st.container()

with chat_container:
    if not st.session_state.rag_messages:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 1rem;
            padding: 2rem;
            text-align: center;
            margin: 2rem 0;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">💬</div>
            <h3 style="color: {COLORS['text_primary']};">Start a conversation</h3>
            <p style="color: {COLORS['text_secondary']};">Ask any question about <strong>{st.session_state.selected_rag_chapter}</strong></p>
            <div style="
                background: {COLORS['bg_primary']};
                border-radius: 0.75rem;
                padding: 1.5rem;
                margin-top: 1.5rem;
                text-align: left;
            ">
                <div style="color: {COLORS['text_secondary']}; font-weight: 600; margin-bottom: 0.75rem;">Example questions:</div>
                <div style="color: {COLORS['text_primary']};">
                    • What are the main functions of...<br>
                    • Explain the pathophysiology of...<br>
                    • What are the differences between X and Y?<br>
                    • Describe the clinical presentation of...
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for message in st.session_state.rag_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about this chapter..."):
    
    chapter = next(c for c in chapters if c['name'] == st.session_state.selected_rag_chapter)
    chapter_id = chapter['id']
    
    st.session_state.rag_messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now().isoformat()
    })
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer, sources = asyncio.run(
                    generate_rag_answer(prompt, chapter_id, num_chunks, temperature)
                )
                
                st.markdown(answer)
                
                assistant_msg = {
                    "role": "assistant",
                    "content": answer,
                    "timestamp": datetime.now().isoformat()
                }
                st.session_state.rag_messages.append(assistant_msg)
                
                storage.append('rag_conversations', {
                    'chapter_id': chapter_id,
                    'chapter_name': st.session_state.selected_rag_chapter,
                    'user_message': prompt,
                    'assistant_message': answer,
                    'num_sources': len(sources)
                })
                
                st.rerun()
                
            except Exception as e:
                logger.error(f"Error generating answer: {e}")
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                
                st.session_state.rag_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().isoformat()
                })