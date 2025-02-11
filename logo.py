import streamlit as st

def show_app_logo():
    """Display the app title and tagline"""
    st.markdown("""
        <style>
        .title-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 0;
            margin: 0.5rem auto;
            max-width: 300px;
            text-align: center;
        }
        .app-title {
            color: #808080;
            font-size: 1.4rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        .app-tagline {
            color: #808080;
            font-size: 0.9rem;
            font-weight: 400;
            letter-spacing: 0.5px;
        }
        </style>
        
        <div class="title-container">
            <div class="app-title">SFSA</div>
            <div class="app-tagline">Smart Financial Statement Analysis</div>
        </div>
    """, unsafe_allow_html=True)
