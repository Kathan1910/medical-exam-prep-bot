# app.py
import streamlit as st
from utils.session_init import init_session_state

st.set_page_config(
    page_title="Medical Exam Prep",
    page_icon="🏥",
    layout="wide"
)

init_session_state()

# Auto-redirect to Dashboard
st.switch_page("pages/1_📊_Dashboard.py")