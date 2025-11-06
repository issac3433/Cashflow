# utils/mobile_css.py
"""Mobile-responsive CSS for Streamlit app"""

MOBILE_CSS = """
<style>
    /* Mobile-first responsive design */
    @media screen and (max-width: 768px) {
        /* Reduce padding and margins on mobile */
        .main .block-container {
            padding: 1rem 1rem 1rem 1rem;
        }
        
        /* Make columns stack on mobile */
        .stColumn {
            width: 100% !important;
            margin-bottom: 1rem;
        }
        
        /* Improve button sizes on mobile */
        button[kind="primary"], button[kind="secondary"] {
            width: 100%;
            padding: 0.75rem;
            font-size: 1rem;
        }
        
        /* Better text input sizing */
        input[type="text"], input[type="number"], textarea {
            font-size: 16px; /* Prevents zoom on iOS */
        }
        
        /* Optimize metrics display */
        .metric-container {
            margin-bottom: 1rem;
        }
        
        /* Better table display on mobile */
        .dataframe {
            font-size: 0.85rem;
            overflow-x: auto;
            display: block;
        }
        
        /* Hide sidebar on very small screens (optional) */
        @media screen and (max-width: 480px) {
            .css-1d391kg {
                display: none;
            }
        }
        
        /* Improve selectbox and dropdown */
        .stSelectbox, .stMultiselect {
            font-size: 16px;
        }
        
        /* Better spacing for expanders */
        .streamlit-expanderHeader {
            font-size: 1rem;
            padding: 0.75rem;
        }
        
        /* Optimize chart containers */
        .js-plotly-plot {
            width: 100% !important;
        }
    }
    
    /* Tablet optimizations */
    @media screen and (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            padding: 2rem 2rem 2rem 2rem;
        }
    }
    
    /* Prevent horizontal scroll on mobile */
    html, body {
        overflow-x: hidden;
        max-width: 100vw;
    }
    
    /* Better touch targets on mobile */
    @media (pointer: coarse) {
        button, .stButton > button {
            min-height: 44px;
            min-width: 44px;
        }
    }
</style>
"""

def inject_mobile_css():
    """Inject mobile CSS into Streamlit app"""
    import streamlit as st
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)

