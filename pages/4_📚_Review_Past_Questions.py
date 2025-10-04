# pages/4_📚_Review_Past_Questions.py
import streamlit as st
import pandas as pd
from datetime import datetime
from config import settings
from utils.logger import setup_logger
from utils.session_init import init_session_state
from utils.design_system import get_global_css, COLORS

logger = setup_logger(__name__)

st.set_page_config(page_title="Review Questions", page_icon="📚", layout="wide")
init_session_state()

# Apply global CSS
st.markdown(get_global_css(), unsafe_allow_html=True)

# Header
st.markdown(f"""
<div style="
    background: {COLORS['gradient_success']};
    padding: 2rem;
    border-radius: 1rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
">
    <h1 style="color: white; margin: 0; font-size: 2.5rem;">📚 Review Past Questions</h1>
    <p style="color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
        Review your practice history and learn from your mistakes
    </p>
</div>
""", unsafe_allow_html=True)

storage = st.session_state.storage
chapters = storage.load('chapters')
questions = storage.load('questions')
attempts = storage.load('attempts')

if not attempts:
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_secondary']};
        border: 2px dashed {COLORS['border']};
        border-radius: 1rem;
        padding: 3rem;
        text-align: center;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">📝</div>
        <h2 style="color: {COLORS['text_primary']};">No practice history yet</h2>
        <p style="color: {COLORS['text_secondary']};">Start practicing questions to see your history here</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Filters Section
st.markdown(f"""
<div style="
    background: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 1rem;
    padding: 1.5rem;
    margin-bottom: 2rem;
">
    <h3 style="margin: 0 0 1rem 0; color: {COLORS['text_primary']};">🔍 Filter Questions</h3>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    filter_chapter = st.selectbox(
        "Chapter",
        options=["All"] + [c['name'] for c in chapters]
    )

with col2:
    filter_correctness = st.selectbox(
        "Status",
        options=["All", "Correct", "Incorrect"]
    )

with col3:
    filter_difficulty = st.selectbox(
        "Difficulty",
        options=["All", "Intermediate", "Advanced", "Complex"]
    )

# Apply filters
filtered_attempts = attempts.copy()

if filter_chapter != "All":
    chapter_id = next(c['id'] for c in chapters if c['name'] == filter_chapter)
    filtered_attempts = [a for a in filtered_attempts if a.get('chapter_id') == chapter_id]

if filter_correctness != "All":
    is_correct = filter_correctness == "Correct"
    filtered_attempts = [a for a in filtered_attempts if a.get('is_correct') == is_correct]

# Get question details
review_data = []
for attempt in filtered_attempts:
    question = next((q for q in questions if q['id'] == attempt['question_id']), None)
    if question:
        if filter_difficulty != "All" and question.get('difficulty', '').title() != filter_difficulty:
            continue
        
        review_data.append({
            'Date': attempt.get('created_at', 'N/A')[:10],
            'Question': question['question'][:100] + '...' if len(question['question']) > 100 else question['question'],
            'Your Answer': attempt['user_answer'],
            'Correct Answer': attempt['correct_answer'],
            'Status': attempt['is_correct'],
            'Difficulty': question.get('difficulty', 'N/A').title(),
            'Question ID': question['id']
        })

if not review_data:
    st.info("No questions match your filters")
    st.stop()

# Results summary
st.markdown(f"""
<div style="
    background: {COLORS['info']}15;
    border-left: 4px solid {COLORS['info']};
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1.5rem;
">
    <strong>Found {len(review_data)} question(s)</strong> matching your filters
</div>
""", unsafe_allow_html=True)

# Display questions as cards
for idx, data in enumerate(review_data):
    # Determine colors based on status
    if data['Status']:
        status_color = COLORS['success']
        status_icon = "✓"
        status_text = "Correct"
        card_bg = f"{COLORS['success']}08"
    else:
        status_color = COLORS['error']
        status_icon = "✗"
        status_text = "Incorrect"
        card_bg = f"{COLORS['error']}08"
    
    # Difficulty badge color
    diff_colors = {
        'Intermediate': COLORS['info'],
        'Advanced': COLORS['warning'],
        'Complex': COLORS['error']
    }
    diff_color = diff_colors.get(data['Difficulty'], COLORS['text_secondary'])
    
    with st.expander(f"{status_icon} Question {idx + 1} - {data['Difficulty']} ({data['Date']})", expanded=False):
        st.markdown(f"""
        <div style="
            background: {card_bg};
            border: 1px solid {status_color}40;
            border-radius: 0.75rem;
            padding: 1.5rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                <div style="flex: 1;">
                    <div style="
                        display: inline-block;
                        background: {diff_color}20;
                        color: {diff_color};
                        padding: 0.25rem 0.75rem;
                        border-radius: 1rem;
                        font-size: 0.75rem;
                        font-weight: 600;
                        margin-bottom: 0.5rem;
                    ">
                        {data['Difficulty']}
                    </div>
                    <div style="
                        display: inline-block;
                        background: {status_color}20;
                        color: {status_color};
                        padding: 0.25rem 0.75rem;
                        border-radius: 1rem;
                        font-size: 0.75rem;
                        font-weight: 600;
                        margin-left: 0.5rem;
                        margin-bottom: 0.5rem;
                    ">
                        {status_icon} {status_text}
                    </div>
                </div>
                <div style="color: {COLORS['text_tertiary']}; font-size: 0.875rem;">
                    {data['Date']}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Get full question details
        question = next(q for q in questions if q['id'] == data['Question ID'])
        
        # Question text
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_primary']};
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        ">
            <h4 style="color: {COLORS['text_primary']}; margin: 0 0 0.5rem 0;">Question:</h4>
            <p style="color: {COLORS['text_primary']}; margin: 0; font-size: 1rem;">
                {question['question']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show image if present
        if question.get('image_path'):
            st.image(question['image_path'], width=500)
        
        # Options
        st.markdown(f"<h4 style='margin: 1rem 0 0.5rem 0; color: {COLORS['text_primary']};'>Options:</h4>", unsafe_allow_html=True)
        
        for key, value in question['options'].items():
            if key == question['correct_answer']:
                bg_color = f"{COLORS['success']}15"
                border_color = COLORS['success']
                icon = "✓"
            elif key == data['Your Answer'] and key != question['correct_answer']:
                bg_color = f"{COLORS['error']}15"
                border_color = COLORS['error']
                icon = "✗"
            else:
                bg_color = COLORS['bg_primary']
                border_color = COLORS['border']
                icon = ""
            
            st.markdown(f"""
            <div style="
                background: {bg_color};
                border: 2px solid {border_color};
                border-radius: 0.5rem;
                padding: 0.75rem 1rem;
                margin-bottom: 0.5rem;
            ">
                <strong>{icon} {key}.</strong> {value}
            </div>
            """, unsafe_allow_html=True)
        
        # Answer summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_tertiary']};
                padding: 1rem;
                border-radius: 0.5rem;
                text-align: center;
            ">
                <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem; margin-bottom: 0.25rem;">Your Answer</div>
                <div style="color: {COLORS['primary']}; font-size: 1.5rem; font-weight: 700;">{data['Your Answer']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="
                background: {COLORS['success']}15;
                padding: 1rem;
                border-radius: 0.5rem;
                text-align: center;
            ">
                <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem; margin-bottom: 0.25rem;">Correct Answer</div>
                <div style="color: {COLORS['success']}; font-size: 1.5rem; font-weight: 700;">{question['correct_answer']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Explanation
        st.markdown(f"""
        <div style="
            background: {COLORS['info']}10;
            border-left: 4px solid {COLORS['info']};
            padding: 1rem;
            border-radius: 0.5rem;
            margin-top: 1rem;
        ">
            <h4 style="color: {COLORS['info']}; margin: 0 0 0.5rem 0;">📚 Explanation</h4>
            <p style="color: {COLORS['text_primary']}; margin: 0; line-height: 1.6;">
                {question['explanation']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # References
        if question.get('citations'):
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_tertiary']};
                padding: 1rem;
                border-radius: 0.5rem;
                margin-top: 1rem;
            ">
                <h4 style="color: {COLORS['text_secondary']}; margin: 0 0 0.5rem 0; font-size: 0.875rem;">📖 References</h4>
                <p style="color: {COLORS['text_secondary']}; margin: 0; font-size: 0.875rem;">
                    {', '.join(question.get('citations', ['No citations']))}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# Export option
st.markdown("---")
if st.button("📥 Export to CSV", type="secondary"):
    df_export = pd.DataFrame(review_data)
    csv = df_export.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"question_review_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )