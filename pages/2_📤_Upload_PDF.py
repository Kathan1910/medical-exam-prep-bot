# pages/2_📤_Upload_PDF.py
import streamlit as st
from pathlib import Path
import asyncio
from core.langchain_pdf_processor import LangchainPDFProcessor
from core.embeddings import EmbeddingManager
from storage.vector_store import LocalVectorStore
from config import settings
from utils.logger import setup_logger
from utils.session_init import init_session_state
from utils.cascade_delete import cascade_delete_chapter
from utils.design_system import get_global_css, COLORS

logger = setup_logger(__name__)

st.set_page_config(page_title="Upload PDF", page_icon="📤", layout="wide")
init_session_state()

# Apply global CSS
st.markdown(get_global_css(), unsafe_allow_html=True)

# Header
st.markdown(f"""
<div style="
    background: {COLORS['gradient_info']};
    padding: 2rem;
    border-radius: 1rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
">
    <h1 style="color: white; margin: 0; font-size: 2.5rem;">📤 Upload Chapter PDF</h1>
    <p style="color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
        Upload medical textbook chapters to create your personalized knowledge base
    </p>
</div>
""", unsafe_allow_html=True)

storage = st.session_state.storage

# Upload Section
st.markdown(f"""
<div style="
    background: {COLORS['bg_secondary']};
    border: 2px solid {COLORS['border']};
    border-radius: 1rem;
    padding: 2rem;
    margin-bottom: 2rem;
">
    <h3 style="margin: 0 0 1rem 0; color: {COLORS['text_primary']};">Upload New Chapter</h3>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type="pdf",
    help="Upload a medical textbook chapter in PDF format",
    label_visibility="collapsed"
)

if uploaded_file:
    st.markdown(f"""
    <div style="
        background: {COLORS['success']}15;
        border-left: 4px solid {COLORS['success']};
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    ">
        <strong style="color: {COLORS['success']};">✓ File selected:</strong> {uploaded_file.name}
    </div>
    """, unsafe_allow_html=True)
    
    # Metadata form
    st.markdown(f"""
    <h4 style="margin: 1.5rem 0 1rem 0; color: {COLORS['text_primary']};">Chapter Details</h4>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        chapter_name = st.text_input(
            "Chapter Name",
            value=uploaded_file.name.replace('.pdf', ''),
            help="Give this chapter a descriptive name"
        )
    
    with col2:
        subject = st.text_input("Subject (optional)", placeholder="e.g., Anatomy, Physiology")
    
    year = st.text_input("Year (optional)", placeholder="e.g., 2024")
    
    # Process button
    if st.button("🚀 Process & Upload", type="primary", use_container_width=True):
        
        if not chapter_name:
            st.error("Please provide a chapter name")
            st.stop()
        
        # Progress tracking
        progress_container = st.container()
        
        with progress_container:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 1rem;
                padding: 2rem;
                margin: 1rem 0;
            ">
                <h4 style="margin: 0 0 1rem 0; color: {COLORS['text_primary']};">Processing PDF...</h4>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        try:
            chapters = storage.load('chapters')
            chapter_id = len(chapters) + 1
            
            # Save PDF
            status_text.markdown(f"**Step 1/4:** Saving PDF file...")
            progress_bar.progress(10)
            
            pdf_path = settings.CHAPTERS_PATH / f"chapter_{chapter_id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            # Extract content
            status_text.markdown(f"**Step 2/4:** Extracting text from PDF...")
            progress_bar.progress(30)
            
            processor = LangchainPDFProcessor()
            chunks = processor.process_pdf(pdf_path, chapter_id)
            
            # Generate embeddings
            status_text.markdown(f"**Step 3/4:** Generating embeddings ({len(chunks)} chunks)...")
            progress_bar.progress(60)
            
            embedding_manager = EmbeddingManager()
            chunk_texts = [chunk['text'] for chunk in chunks]
            
            async def get_embeddings():
                return await embedding_manager.batch_embed(chunk_texts)
            
            embeddings = asyncio.run(get_embeddings())
            
            # Store in vector database
            status_text.markdown(f"**Step 4/4:** Storing in vector database...")
            progress_bar.progress(85)
            
            vector_store = LocalVectorStore()
            vector_store.load(settings.EMBEDDINGS_PATH)
            vector_store.add_embeddings(embeddings, chunks)
            vector_store.save(settings.EMBEDDINGS_PATH)
            
            # Save metadata
            chapter_data = {
                'id': chapter_id,
                'name': chapter_name,
                'filename': uploaded_file.name,
                'pdf_path': str(pdf_path),
                'num_chunks': len(chunks),
                'subject': subject if subject else None,
                'year': year if year else None
            }
            
            storage.append('chapters', chapter_data)
            
            progress_bar.progress(100)
            status_text.empty()
            
            # Success message
            st.balloons()
            st.markdown(f"""
            <div style="
                background: {COLORS['success']}15;
                border: 2px solid {COLORS['success']};
                border-radius: 1rem;
                padding: 2rem;
                margin: 1rem 0;
            ">
                <h3 style="color: {COLORS['success']}; margin: 0 0 1rem 0;">✓ Success!</h3>
                <p style="margin: 0; color: {COLORS['text_primary']};">
                    <strong>"{chapter_name}"</strong> processed successfully!
                </p>
                <div style="
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 1rem;
                    margin-top: 1rem;
                ">
                    <div style="background: white; padding: 1rem; border-radius: 0.5rem;">
                        <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem;">Text Chunks</div>
                        <div style="color: {COLORS['primary']}; font-size: 1.5rem; font-weight: 700;">{len(chunks)}</div>
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 0.5rem;">
                        <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem;">Embeddings</div>
                        <div style="color: {COLORS['primary']}; font-size: 1.5rem; font-weight: 700;">{len(embeddings)}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            st.markdown(f"""
            <div style="
                background: {COLORS['error']}15;
                border-left: 4px solid {COLORS['error']};
                padding: 1.5rem;
                border-radius: 0.5rem;
            ">
                <strong style="color: {COLORS['error']};">Error:</strong> {str(e)}
            </div>
            """, unsafe_allow_html=True)

# Existing Chapters Section
st.markdown("---")
st.markdown(f"""
<h2 style="color: {COLORS['text_primary']}; margin: 2rem 0 1rem 0;">📚 Your Chapters</h2>
""", unsafe_allow_html=True)

chapters = storage.load('chapters')

if chapters:
    for chapter in chapters:
        # Chapter card
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: {COLORS['text_tertiary']}22 0 4px 6px;
            transition: all 0.3s ease;
        " onmouseover="this.style.boxShadow='0 8px 12px rgba(0,0,0,0.1)'" onmouseout="this.style.boxShadow='0 4px 6px rgba(0,0,0,0.05)'">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                <div>
                    <h3 style="margin: 0; color: {COLORS['text_primary']};">📖 {chapter['name']}</h3>
                    <p style="margin: 0.5rem 0 0 0; color: {COLORS['text_secondary']}; font-size: 0.875rem;">
                        {chapter.get('filename', 'Unknown file')}
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem;">CHUNKS</div>
                <div style="color: {COLORS['primary']}; font-size: 1.5rem; font-weight: 700;">{chapter.get('num_chunks', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center;">
                <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem;">ID</div>
                <div style="color: {COLORS['primary']}; font-size: 1.5rem; font-weight: 700;">{chapter['id']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if chapter.get('subject'):
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem;">SUBJECT</div>
                    <div style="color: {COLORS['info']}; font-size: 1rem; font-weight: 600;">{chapter['subject']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            if chapter.get('year'):
                st.markdown(f"""
                <div style="text-align: center;">
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.75rem;">YEAR</div>
                    <div style="color: {COLORS['info']}; font-size: 1rem; font-weight: 600;">{chapter['year']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Delete button
        delete_col1, delete_col2 = st.columns([5, 1])
        
        with delete_col2:
            if st.button("🗑️ Delete", key=f"delete_{chapter['id']}", type="secondary", use_container_width=True):
                st.session_state[f'confirm_delete_{chapter["id"]}'] = True
        
        # Confirmation dialog
        if st.session_state.get(f'confirm_delete_{chapter["id"]}', False):
            st.markdown(f"""
            <div style="
                background: {COLORS['warning']}15;
                border: 2px solid {COLORS['warning']};
                border-radius: 0.75rem;
                padding: 1.5rem;
                margin: 1rem 0;
            ">
                <h4 style="color: {COLORS['warning']}; margin: 0 0 0.5rem 0;">⚠️ Confirm Deletion</h4>
                <p style="margin: 0; color: {COLORS['text_primary']};">
                    Delete <strong>"{chapter['name']}"</strong>?<br>
                    This will permanently remove: PDF, questions, attempts, RAG conversations, and embeddings.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            confirm_col1, confirm_col2 = st.columns(2)
            
            with confirm_col1:
                if st.button("✓ Yes, Delete", key=f"confirm_yes_{chapter['id']}", type="primary", use_container_width=True):
                    with st.spinner("Deleting..."):
                        stats = cascade_delete_chapter(chapter['id'], storage)
                        
                        if stats['chapter_deleted']:
                            st.success(f"Chapter deleted: {stats['questions_deleted']} questions, {stats['attempts_deleted']} attempts removed")
                            del st.session_state[f'confirm_delete_{chapter["id"]}']
                            st.rerun()
                        else:
                            st.error("Failed to delete chapter")
            
            with confirm_col2:
                if st.button("✗ Cancel", key=f"confirm_no_{chapter['id']}", use_container_width=True):
                    del st.session_state[f'confirm_delete_{chapter["id"]}']
                    st.rerun()
else:
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_secondary']};
        border: 2px dashed {COLORS['border']};
        border-radius: 1rem;
        padding: 3rem;
        text-align: center;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📚</div>
        <h3 style="color: {COLORS['text_secondary']};">No chapters uploaded yet</h3>
        <p style="color: {COLORS['text_tertiary']};">Upload your first chapter above to get started</p>
    </div>
    """, unsafe_allow_html=True)