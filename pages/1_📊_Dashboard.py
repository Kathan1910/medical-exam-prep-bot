# pages/1_📊_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from config import settings
from utils.logger import setup_logger
from utils.session_init import init_session_state
from utils.design_system import get_global_css, COLORS

logger = setup_logger(__name__)

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
init_session_state()

# Apply global CSS
st.markdown(get_global_css(), unsafe_allow_html=True)

# Load data
storage = st.session_state.storage
chapters = storage.load('chapters')
questions = storage.load('questions')
attempts = storage.load('attempts')
rag_conversations = storage.load('rag_conversations')

# Header with gradient
st.markdown(f"""
<div style="
    background: {COLORS['gradient_primary']};
    padding: 2rem;
    border-radius: 1rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
">
    <h1 style="color: white; margin: 0; font-size: 2.5rem;">Medical Exam Prep Dashboard</h1>
    <p style="color: rgba(255, 255, 255, 0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
        Track your progress and master your medical knowledge
    </p>
</div>
""", unsafe_allow_html=True)

# Welcome message if no data
if not chapters:
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_secondary']};
        border: 2px dashed {COLORS['border']};
        border-radius: 1rem;
        padding: 3rem;
        text-align: center;
    ">
        <h2 style="color: {COLORS['text_primary']};">Welcome to Medical Exam Prep! 👋</h2>
        <p style="color: {COLORS['text_secondary']}; font-size: 1.1rem; margin: 1rem 0;">
            Start by uploading a chapter PDF from the sidebar menu to begin your journey
        </p>
        <p style="color: {COLORS['text_tertiary']};">
            📤 Upload PDF → ❓ Generate Questions → 📝 Practice → 📊 Track Progress
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Top metrics with modern cards
st.markdown("### 📈 Quick Stats")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 1rem; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="font-size: 0.875rem; opacity: 0.9; font-weight: 600;">CHAPTERS</div>
        <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">{len(chapters)}</div>
        <div style="font-size: 0.875rem; opacity: 0.8;">Uploaded</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.5rem; border-radius: 1rem; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="font-size: 0.875rem; opacity: 0.9; font-weight: 600;">QUESTIONS</div>
        <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">{len(questions)}</div>
        <div style="font-size: 0.875rem; opacity: 0.8;">Generated</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    if attempts:
        correct = sum(1 for a in attempts if a.get('is_correct', False))
        accuracy = (correct / len(attempts)) * 100
        color_gradient = "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)" if accuracy >= 70 else "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
        st.markdown(f"""
        <div style="background: {color_gradient}; padding: 1.5rem; border-radius: 1rem; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="font-size: 0.875rem; opacity: 0.9; font-weight: 600;">ACCURACY</div>
            <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">{accuracy:.1f}%</div>
            <div style="font-size: 0.875rem; opacity: 0.8;">{correct}/{len(attempts)} Correct</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 1.5rem; border-radius: 1rem; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="font-size: 0.875rem; opacity: 0.9; font-weight: 600;">ACCURACY</div>
            <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">N/A</div>
            <div style="font-size: 0.875rem; opacity: 0.8;">No attempts yet</div>
        </div>
        """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); padding: 1.5rem; border-radius: 1rem; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="font-size: 0.875rem; opacity: 0.9; font-weight: 600;">RAG QUERIES</div>
        <div style="font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0;">{len(rag_conversations)}</div>
        <div style="font-size: 0.875rem; opacity: 0.8;">Conversations</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if not attempts:
    st.info("📝 No practice data yet. Generate and answer questions to see detailed analytics!")
    st.stop()

# Modern tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Performance", 
    "📚 Chapters", 
    "🎯 Difficulty",
    "📅 Timeline"
])

# TAB 1: Performance Overview
with tab1:
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        correct_count = sum(1 for a in attempts if a.get('is_correct', False))
        incorrect_count = len(attempts) - correct_count
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Correct', 'Incorrect'],
            values=[correct_count, incorrect_count],
            hole=0.65,
            marker=dict(colors=[COLORS['success'], COLORS['error']]),
            textinfo='label+percent',
            textfont_size=16,
            textfont_color='white'
        )])
        
        fig_donut.update_layout(
            showlegend=True,
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=14, color=COLORS['text_primary']),
            annotations=[dict(
                text=f'<b>{(correct_count/len(attempts)*100):.0f}%</b>',
                x=0.5, y=0.5,
                font_size=48,
                showarrow=False,
                font=dict(color=COLORS['success'] if correct_count > incorrect_count else COLORS['error'])
            )]
        )
        
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with col_right:
        total_attempts = len(attempts)
        accuracy = (correct_count / total_attempts) * 100
        
        if accuracy >= 80:
            rating = "Excellent"
            color = COLORS['success']
            emoji = "🌟"
        elif accuracy >= 70:
            rating = "Good"
            color = COLORS['info']
            emoji = "✅"
        elif accuracy >= 60:
            rating = "Fair"
            color = COLORS['warning']
            emoji = "⚠️"
        else:
            rating = "Needs Work"
            color = COLORS['error']
            emoji = "📚"
        
        st.markdown(f"""
        <div style="
            background: {color}15;
            padding: 2rem;
            border-radius: 1rem;
            border-left: 5px solid {color};
            margin-bottom: 1.5rem;
        ">
            <div style="font-size: 3rem; text-align: center; margin-bottom: 0.5rem;">{emoji}</div>
            <h2 style="color: {color}; margin: 0; text-align: center; font-size: 1.75rem;">{rating}</h2>
            <p style="text-align: center; color: {COLORS['text_secondary']}; margin: 0.5rem 0 0 0;">
                Based on {total_attempts} attempts
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Stats cards
        stats = [
            ("Total Attempts", total_attempts, "📝"),
            ("Correct", correct_count, "✅"),
            ("Incorrect", incorrect_count, "❌"),
        ]
        
        for label, value, emoji in stats:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_primary']};
                padding: 1rem;
                border-radius: 0.75rem;
                border: 1px solid {COLORS['border']};
                margin-bottom: 0.75rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div>
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem; font-weight: 600;">{label}</div>
                    <div style="color: {COLORS['text_primary']}; font-size: 1.5rem; font-weight: 700;">{value}</div>
                </div>
                <div style="font-size: 2rem;">{emoji}</div>
            </div>
            """, unsafe_allow_html=True)

# TAB 2: Chapter Analysis
with tab2:
    chapter_stats = []
    for chapter in chapters:
        chapter_attempts = [a for a in attempts if a.get('chapter_id') == chapter['id']]
        if chapter_attempts:
            correct = sum(1 for a in chapter_attempts if a.get('is_correct', False))
            accuracy = (correct / len(chapter_attempts) * 100)
            chapter_stats.append({
                'Chapter': chapter['name'][:40] + '...' if len(chapter['name']) > 40 else chapter['name'],
                'Attempts': len(chapter_attempts),
                'Correct': correct,
                'Incorrect': len(chapter_attempts) - correct,
                'Accuracy': accuracy
            })
    
    if chapter_stats:
        df_chapters = pd.DataFrame(chapter_stats)
        
        fig_chapters = go.Figure()
        
        fig_chapters.add_trace(go.Bar(
            name='Correct',
            y=df_chapters['Chapter'],
            x=df_chapters['Correct'],
            orientation='h',
            marker=dict(
                color=df_chapters['Accuracy'],
                colorscale=[[0, '#EF4444'], [0.5, '#F59E0B'], [1, '#10B981']],
                showscale=True,
                colorbar=dict(title="Accuracy %", len=0.5)
            ),
            text=df_chapters['Correct'],
            textposition='inside',
            textfont=dict(color='white', size=14),
            hovertemplate='<b>%{y}</b><br>Correct: %{x}<br>Accuracy: %{marker.color:.1f}%<extra></extra>'
        ))
        
        fig_chapters.add_trace(go.Bar(
            name='Incorrect',
            y=df_chapters['Chapter'],
            x=df_chapters['Incorrect'],
            orientation='h',
            marker=dict(color='#FCA5A5'),
            text=df_chapters['Incorrect'],
            textposition='inside',
            textfont=dict(color='white', size=14)
        ))
        
        fig_chapters.update_layout(
            barmode='stack',
            height=max(350, len(chapter_stats) * 70),
            xaxis_title="Number of Attempts",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=13, color=COLORS['text_primary']),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig_chapters, use_container_width=True)

# TAB 3: Difficulty Breakdown
with tab3:
    difficulty_stats = {'intermediate': [], 'advanced': [], 'complex': []}
    
    for attempt in attempts:
        question = next((q for q in questions if q['id'] == attempt['question_id']), None)
        if question:
            diff = question.get('difficulty', 'intermediate').lower()
            if diff in difficulty_stats:
                difficulty_stats[diff].append(attempt.get('is_correct', False))
    
    diff_data = []
    for diff, results in difficulty_stats.items():
        if results:
            accuracy = sum(results) / len(results) * 100
            diff_data.append({
                'Difficulty': diff.title(),
                'Attempts': len(results),
                'Correct': sum(results),
                'Incorrect': len(results) - sum(results),
                'Accuracy': accuracy
            })
    
    if diff_data:
        df_diff = pd.DataFrame(diff_data)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_diff = go.Figure()
            
            fig_diff.add_trace(go.Bar(
                name='Correct',
                x=df_diff['Difficulty'],
                y=df_diff['Correct'],
                marker_color=COLORS['success'],
                text=df_diff['Correct'],
                textposition='outside',
                textfont=dict(size=14)
            ))
            
            fig_diff.add_trace(go.Bar(
                name='Incorrect',
                x=df_diff['Difficulty'],
                y=df_diff['Incorrect'],
                marker_color=COLORS['error'],
                text=df_diff['Incorrect'],
                textposition='outside',
                textfont=dict(size=14)
            ))
            
            fig_diff.update_layout(
                barmode='group',
                height=400,
                xaxis_title="Difficulty Level",
                yaxis_title="Number of Attempts",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(size=13, color=COLORS['text_primary'])
            )
            
            st.plotly_chart(fig_diff, use_container_width=True)
        
        with col2:
            for _, row in df_diff.iterrows():
                color = COLORS['success'] if row['Accuracy'] >= 70 else COLORS['warning'] if row['Accuracy'] >= 60 else COLORS['error']
                st.markdown(f"""
                <div style="
                    background: {color}15;
                    padding: 1.5rem;
                    border-radius: 0.75rem;
                    margin-bottom: 1rem;
                    border-left: 4px solid {color};
                ">
                    <h4 style="margin: 0; color: {color}; font-size: 1.1rem;">{row['Difficulty']}</h4>
                    <div style="font-size: 2.5rem; font-weight: 700; color: {color}; margin: 0.5rem 0;">
                        {row['Accuracy']:.0f}%
                    </div>
                    <div style="color: {COLORS['text_secondary']}; font-size: 0.875rem;">
                        {row['Attempts']} attempts
                    </div>
                </div>
                """, unsafe_allow_html=True)

# TAB 4: Progress Timeline
with tab4:
    attempts_with_dates = []
    for attempt in attempts:
        if 'created_at' in attempt:
            date = attempt['created_at'][:10]
            attempts_with_dates.append({
                'Date': date,
                'Correct': 1 if attempt.get('is_correct') else 0,
                'Total': 1
            })
    
    if attempts_with_dates:
        df_time = pd.DataFrame(attempts_with_dates)
        df_time_grouped = df_time.groupby('Date').agg({
            'Correct': 'sum',
            'Total': 'sum'
        }).reset_index()
        df_time_grouped['Accuracy'] = (df_time_grouped['Correct'] / df_time_grouped['Total'] * 100)
        df_time_grouped['Date'] = pd.to_datetime(df_time_grouped['Date'])
        
        fig_timeline = go.Figure()
        
        fig_timeline.add_trace(go.Scatter(
            x=df_time_grouped['Date'],
            y=df_time_grouped['Accuracy'],
            mode='lines+markers',
            name='Accuracy',
            line=dict(color=COLORS['primary'], width=4),
            marker=dict(size=12, color=COLORS['primary'], line=dict(width=2, color='white')),
            fill='tozeroy',
            fillcolor=f'rgba(79, 70, 229, 0.1)',
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Accuracy: %{y:.1f}%<br>Attempts: %{text}<extra></extra>',
            text=df_time_grouped['Total']
        ))
        
        fig_timeline.add_hline(
            y=70, 
            line_dash="dash", 
            line_color=COLORS['success'],
            annotation_text="Target: 70%",
            annotation_position="right"
        )
        
        fig_timeline.update_layout(
            height=450,
            xaxis_title="Date",
            yaxis_title="Accuracy (%)",
            yaxis=dict(range=[0, 100]),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=13, color=COLORS['text_primary']),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)