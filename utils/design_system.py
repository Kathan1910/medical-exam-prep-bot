# utils/design_system.py
"""
Modern Design System for Medical Exam Prep Application
Production-ready UI components and styling
"""

# Color Palette
COLORS = {
    'primary': '#4F46E5',      # Indigo
    'secondary': '#06B6D4',    # Cyan
    'success': '#10B981',      # Green
    'warning': '#F59E0B',      # Amber
    'error': '#EF4444',        # Red
    'info': '#3B82F6',         # Blue
    
    # Neutrals
    'bg_primary': '#FFFFFF',
    'bg_secondary': '#F9FAFB',
    'bg_tertiary': '#F3F4F6',
    'text_primary': '#111827',
    'text_secondary': '#6B7280',
    'text_tertiary': '#9CA3AF',
    'border': '#E5E7EB',
    
    # Gradients
    'gradient_primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'gradient_success': 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
    'gradient_info': 'linear-gradient(135deg, #3B82F6 0%, #2563EB 100%)',
}

# Typography
FONTS = {
    'heading': '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    'body': '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    'mono': '"Fira Code", "Courier New", monospace'
}

# Spacing
SPACING = {
    'xs': '0.25rem',
    'sm': '0.5rem',
    'md': '1rem',
    'lg': '1.5rem',
    'xl': '2rem',
    '2xl': '3rem',
}

# Border Radius
RADIUS = {
    'sm': '0.375rem',
    'md': '0.5rem',
    'lg': '0.75rem',
    'xl': '1rem',
    'full': '9999px',
}

# Shadows
SHADOWS = {
    'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
}

def get_global_css():
    """Return global CSS for the entire application"""
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* Global Styles */
        * {{
            font-family: {FONTS['body']};
        }}
        
        /* Hide Streamlit Branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {COLORS['bg_tertiary']};
            border-radius: {RADIUS['full']};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {COLORS['text_tertiary']};
            border-radius: {RADIUS['full']};
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS['text_secondary']};
        }}
        
        /* Main Container */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }}
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            font-family: {FONTS['heading']};
            font-weight: 700;
            color: {COLORS['text_primary']};
        }}
        
        /* Metrics */
        [data-testid="stMetric"] {{
            background: {COLORS['bg_primary']};
            padding: {SPACING['lg']};
            border-radius: {RADIUS['lg']};
            border: 1px solid {COLORS['border']};
            box-shadow: {SHADOWS['sm']};
            transition: all 0.3s ease;
        }}
        
        [data-testid="stMetric"]:hover {{
            box-shadow: {SHADOWS['md']};
            transform: translateY(-2px);
        }}
        
        [data-testid="stMetricValue"] {{
            font-size: 2rem;
            font-weight: 700;
            color: {COLORS['primary']};
        }}
        
        [data-testid="stMetricLabel"] {{
            font-size: 0.875rem;
            font-weight: 500;
            color: {COLORS['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        /* Buttons */
        .stButton > button {{
            border-radius: {RADIUS['md']};
            font-weight: 600;
            padding: 0.625rem 1.25rem;
            transition: all 0.2s ease;
            border: none;
            box-shadow: {SHADOWS['sm']};
        }}
        
        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: {SHADOWS['md']};
        }}
        
        .stButton > button[kind="primary"] {{
            background: {COLORS['gradient_primary']};
        }}
        
        /* Input Fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div,
        .stSelectbox > div > div > div,
        .stNumberInput > div > div > input {{
            border-radius: {RADIUS['md']};
            border: 1px solid {COLORS['border']};
            padding: 0.625rem;
            font-size: 0.875rem;
            color: {COLORS['text_primary']} !important;
            background-color: {COLORS['bg_primary']} !important;
        }}
        
        /* Selectbox - force dark text everywhere */
        .stSelectbox [data-baseweb="select"] > div,
        .stSelectbox [data-baseweb="select"] span,
        .stSelectbox [data-baseweb="select"] {{
            color: {COLORS['text_primary']} !important;
            font-weight: 500 !important;
        }}
        
        /* Selectbox selected value */
        .stSelectbox [data-baseweb="select"] [role="button"] > div {{
            color: {COLORS['text_primary']} !important;
        }}
        
        /* Number input text color */
        .stNumberInput input {{
            color: {COLORS['text_primary']} !important;
            font-weight: 500 !important;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: {COLORS['primary']};
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2rem;
            background-color: transparent;
            border-bottom: 2px solid {COLORS['border']};
        }}
        
        .stTabs [data-baseweb="tab"] {{
            height: 3rem;
            padding: 0 1rem;
            background-color: transparent;
            border-radius: {RADIUS['md']} {RADIUS['md']} 0 0;
            color: {COLORS['text_secondary']};
            font-weight: 600;
            border: none;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: transparent;
            color: {COLORS['primary']};
            border-bottom: 3px solid {COLORS['primary']};
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {COLORS['bg_secondary']};
            border-radius: {RADIUS['md']};
            font-weight: 600;
            padding: {SPACING['md']};
            border: 1px solid {COLORS['border']};
        }}
        
        .streamlit-expanderHeader:hover {{
            background-color: {COLORS['bg_tertiary']};
        }}
        
        /* Chat Messages */
        .stChatMessage {{
            background-color: {COLORS['bg_secondary']};
            border-radius: {RADIUS['lg']};
            padding: {SPACING['lg']};
            margin-bottom: {SPACING['md']};
            border: 1px solid {COLORS['border']};
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {COLORS['bg_secondary']};
            border-right: 1px solid {COLORS['border']};
        }}
        
        [data-testid="stSidebar"] .stSelectbox {{
            background-color: {COLORS['bg_primary']};
            border-radius: {RADIUS['md']};
            padding: {SPACING['sm']};
        }}
        
        /* Progress Bar */
        .stProgress > div > div > div > div {{
            background: {COLORS['gradient_primary']};
            border-radius: {RADIUS['full']};
        }}
        
        /* Info/Warning/Error Boxes */
        .stAlert {{
            border-radius: {RADIUS['md']};
            border-left-width: 4px;
            padding: {SPACING['lg']};
        }}
        
        /* Dataframe */
        .stDataFrame {{
            border-radius: {RADIUS['md']};
            overflow: hidden;
            border: 1px solid {COLORS['border']};
        }}
        
        /* File Uploader */
        [data-testid="stFileUploader"] {{
            background-color: {COLORS['bg_secondary']};
            border: 2px dashed {COLORS['border']};
            border-radius: {RADIUS['lg']};
            padding: {SPACING['xl']};
            transition: all 0.3s ease;
        }}
        
        [data-testid="stFileUploader"]:hover {{
            border-color: {COLORS['primary']};
            background-color: rgba(79, 70, 229, 0.05);
        }}
        
        /* Custom Classes */
        .card {{
            background: {COLORS['bg_primary']};
            border-radius: {RADIUS['lg']};
            padding: {SPACING['xl']};
            box-shadow: {SHADOWS['md']};
            border: 1px solid {COLORS['border']};
            margin-bottom: {SPACING['md']};
        }}
        
        .card-header {{
            font-size: 1.25rem;
            font-weight: 700;
            color: {COLORS['text_primary']};
            margin-bottom: {SPACING['md']};
            padding-bottom: {SPACING['md']};
            border-bottom: 2px solid {COLORS['border']};
        }}
        
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: {RADIUS['full']};
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .badge-success {{
            background-color: rgba(16, 185, 129, 0.1);
            color: {COLORS['success']};
        }}
        
        .badge-warning {{
            background-color: rgba(245, 158, 11, 0.1);
            color: {COLORS['warning']};
        }}
        
        .badge-error {{
            background-color: rgba(239, 68, 68, 0.1);
            color: {COLORS['error']};
        }}
        
        .badge-info {{
            background-color: rgba(59, 130, 246, 0.1);
            color: {COLORS['info']};
        }}
    </style>
    """

def create_metric_card(title, value, delta=None, icon="", color="primary"):
    """Create a styled metric card"""
    delta_html = ""
    if delta is not None:
        delta_color = COLORS['success'] if delta >= 0 else COLORS['error']
        delta_symbol = "↑" if delta >= 0 else "↓"
        delta_html = f"""
        <div style="color: {delta_color}; font-size: 0.875rem; font-weight: 600; margin-top: 0.5rem;">
            {delta_symbol} {abs(delta):.1f}%
        </div>
        """
    
    return f"""
    <div style="
        background: {COLORS['bg_primary']};
        border-radius: {RADIUS['lg']};
        padding: {SPACING['lg']};
        border: 1px solid {COLORS['border']};
        box-shadow: {SHADOWS['md']};
        transition: all 0.3s ease;
    ">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: {SPACING['sm']};">
            <span style="color: {COLORS['text_secondary']}; font-size: 0.875rem; font-weight: 600; text-transform: uppercase;">
                {title}
            </span>
            <span style="font-size: 1.5rem;">{icon}</span>
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: {COLORS[color]};">
            {value}
        </div>
        {delta_html}
    </div>
    """

def create_stat_badge(label, value, badge_type="info"):
    """Create a small stat badge"""
    return f"""
    <span class="badge badge-{badge_type}">
        {label}: {value}
    </span>
    """