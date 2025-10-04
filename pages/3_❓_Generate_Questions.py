# pages/3_❓_Generate_Questions.py
import streamlit as st
import asyncio
from core.agents.question_generator import QuestionGeneratorAgent
from config import settings
from utils.logger import setup_logger
from utils.session_init import init_session_state

logger = setup_logger(__name__)

st.set_page_config(page_title="Generate Questions", page_icon="❓", layout="wide")
init_session_state()

storage = st.session_state.storage
chapters = storage.load('chapters')

st.title("❓ Generate Practice Questions")

if not chapters:
    st.warning("⚠️ Please upload at least one chapter first!")
    st.stop()

# Configuration Section
st.subheader("⚙️ Configuration")

col1, col2, col3 = st.columns(3)

with col1:
    selected_chapter = st.selectbox(
        "Select Chapter",
        options=[c['name'] for c in chapters],
        help="Choose which chapter to generate questions from"
    )

with col2:
    num_questions = st.number_input(
        "Number of Questions",
        min_value=1,
        max_value=50,
        value=5,
        help="How many questions to generate"
    )

with col3:
    difficulty = st.selectbox(
        "Difficulty Level",
        options=["Intermediate", "Advanced", "Complex"],
        help="Select question difficulty"
    )

include_images = st.checkbox(
    "Include image-based questions",
    value=True,
    help="Generate questions that reference medical images"
)

# Add batch size option
with st.expander("⚡ Advanced Settings"):
    batch_size = st.slider(
        "Concurrent Generation (questions at a time)",
        min_value=1,
        max_value=5,
        value=3,
        help="Generate multiple questions simultaneously. Higher = faster but more API usage."
    )

# Generate button
if st.button("🎯 Generate Questions", type="primary", use_container_width=True):
    
    chapter_id = next(c['id'] for c in chapters if c['name'] == selected_chapter)
    
    with st.spinner("🔄 Generating questions..."):
        
        progress_bar = st.progress(0)
        status_container = st.empty()
        questions_container = st.container()
        
        agent = QuestionGeneratorAgent()
        generated_count = 0
        failed_count = 0
        
        # Calculate batches
        total_batches = (num_questions + batch_size - 1) // batch_size
        
        # Generate in batches
        for batch_num in range(total_batches):
            remaining = num_questions - generated_count
            current_batch_size = min(batch_size, remaining)
            
            status_container.info(
                f"🔄 Generating batch {batch_num + 1}/{total_batches} "
                f"({current_batch_size} questions simultaneously)..."
            )
            
            # Use batch generation method
            try:
                batch_results = asyncio.run(
                    agent.generate_batch_questions(
                        chapter_id=chapter_id,
                        count=current_batch_size,
                        difficulty=difficulty.lower(),
                        include_images=include_images,
                        max_concurrent=current_batch_size
                    )
                )
                
                # Process results
                for result in batch_results:
                    question_num = generated_count + 1
                    
                    if result:
                        # Save question
                        storage.append('questions', result)
                        generated_count += 1
                        
                        # Display preview
                        with questions_container:
                            with st.expander(f"✅ Question {question_num} - Preview"):
                                st.markdown(f"**Q:** {result['question'][:150]}...")
                                st.write(f"**Difficulty:** {result['difficulty']}")
                                st.write(f"**Confidence:** {result.get('confidence_score', 'N/A')}%")
                    else:
                        failed_count += 1
                        st.warning(f"⚠️ Failed to generate question {question_num}")
                
            except Exception as e:
                logger.error(f"Error in batch generation: {e}")
                st.error(f"Batch {batch_num + 1} failed: {str(e)}")
                failed_count += current_batch_size
            
            # Update progress
            progress_bar.progress(generated_count / num_questions)
        
        status_container.empty()
        
        # Summary
        st.success(f"""
        ### ✅ Generation Complete!
        - **Generated:** {generated_count} questions
        - **Failed:** {failed_count} questions
        - **Time saved:** ~{(num_questions * 10 - generated_count * 3)}+ seconds with batch processing!
        """)

# Practice Section (rest of your existing code stays the same)
st.markdown("---")
st.subheader("📝 Practice Mode")

chapter_id = next(c['id'] for c in chapters if c['name'] == selected_chapter)
chapter_questions = storage.filter('questions', chapter_id=chapter_id)

if not chapter_questions:
    st.info("No questions available. Generate some questions first!")
    st.stop()

# Initialize navigation index
if 'current_question_idx' not in st.session_state:
    st.session_state.current_question_idx = 0

# Question navigation
total_questions = len(chapter_questions)
current_idx = st.session_state.current_question_idx

# Ensure index is within bounds
if current_idx >= total_questions:
    st.session_state.current_question_idx = 0
    current_idx = 0
elif current_idx < 0:
    st.session_state.current_question_idx = 0
    current_idx = 0

current_question = chapter_questions[current_idx]

# Display question number with navigation
col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
with col_nav2:
    st.markdown(f"### Question {current_idx + 1} of {total_questions}")

# Show image if present
if current_question.get('image_path'):
    st.image(current_question['image_path'], width=500)

st.markdown(f"**{current_question['question']}**")

# Options
selected_answer = st.radio(
    "Select your answer:",
    options=list(current_question['options'].keys()),
    format_func=lambda x: f"{x}. {current_question['options'][x]}",
    key=f"answer_{current_question['id']}"
)

# Navigation buttons
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("⬅️ Previous Question", use_container_width=True, disabled=(current_idx == 0)):
        st.session_state.current_question_idx = max(0, current_idx - 1)
        st.session_state.show_answer = False
        st.rerun()

with col2:
    if st.button("✅ Submit Answer", use_container_width=True):
        st.session_state.show_answer = True
        
        # Record attempt
        is_correct = selected_answer == current_question['correct_answer']
        
        attempt = {
            'question_id': current_question['id'],
            'chapter_id': chapter_id,
            'user_answer': selected_answer,
            'correct_answer': current_question['correct_answer'],
            'is_correct': is_correct
        }
        
        storage.append('attempts', attempt)

with col3:
    if st.button("➡️ Next Question", use_container_width=True, disabled=(current_idx == total_questions - 1)):
        st.session_state.current_question_idx = min(total_questions - 1, current_idx + 1)
        st.session_state.show_answer = False
        st.rerun()

# Show answer if submitted
if st.session_state.get('show_answer', False):
    is_correct = selected_answer == current_question['correct_answer']
    
    if is_correct:
        st.success("✅ **Correct!**")
    else:
        st.error(f"❌ **Incorrect.** The correct answer is: **{current_question['correct_answer']}**")
    
    # Enhanced Explanation
    st.info(f"""
    **📚 Detailed Explanation:**
    
    {current_question['explanation']}
    
    **📖 References:**
    {', '.join(current_question.get('citations', ['No citations']))}
    
    **🎯 Key Concepts:** {', '.join(current_question.get('key_concepts', ['N/A']))}
    """)