import streamlit as st
from .phonepe import show_phonepe_page
from .googlepay import show_googlepay_page
from .paytm import show_paytm_page
from .supermoney import show_supermoney_page
from support import show_support_form
import time

def show_platform_grid():
    """Show all platforms in a grid layout"""
    st.markdown("""
        <style>
        .platform-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 0.5rem;
            padding: 0.5rem;
            margin-top: 1rem;
        }
        .platform-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 0.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .platform-card:hover {
            transform: translateY(-2px);
            background: rgba(255, 255, 255, 0.1);
        }
        .platform-icon {
            font-size: 1.5rem;
            margin-bottom: 0.3rem;
        }
        .platform-name {
            color: #ffffff;
            font-size: 0.8rem;
        }
        .active-platform {
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .stButton button {
            padding: 0.3rem 0.5rem !important;
            font-size: 0.8rem !important;
            min-height: 0px !important;
            height: auto !important;
            width: 100%;
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: none !important;
            margin: 0 !important;
        }
        .stButton button:hover {
            background-color: rgba(255, 255, 255, 0.1) !important;
            transform: translateY(-1px);
        }
        .utility-buttons {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
            justify-content: center;
        }
        .help-button button {
            background-color: rgba(0, 123, 255, 0.1) !important;
            color: #0077ff !important;
        }
        .logout-button button {
            background-color: rgba(255, 59, 48, 0.1) !important;
            color: #ff3b30 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    platforms = {
        'PhonePe': '📱',
        'Paytm': '💰',
        'SuperMoney': '💸',
        'Google Pay': '💳',
        'Amazon Pay': '🛒',
        'BHIM': '🇮🇳',
        'WhatsApp Pay': '💬',
        'Other': '🔄'
    }

    # Remove currently selected platform from the grid
    current_platform = st.session_state.get('selected_platform')
    if current_platform:
        platforms_to_show = {k: v for k, v in platforms.items() if k != current_platform}
    else:
        platforms_to_show = platforms

    st.markdown('<div class="platform-grid">', unsafe_allow_html=True)
    
    # Calculate number of columns based on remaining platforms
    num_platforms = len(platforms_to_show)
    num_cols = min(6, num_platforms)  # Use fewer columns if fewer platforms
    cols = st.columns(num_cols)
    
    for idx, (platform, icon) in enumerate(platforms_to_show.items()):
        with cols[idx % num_cols]:
            active_class = "active-platform" if platform == st.session_state.get('selected_platform', '') else ""
            if st.button(f"{icon}\n{platform}", key=f"btn_{platform}", use_container_width=True):
                st.session_state.selected_platform = platform
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add Help and Logout buttons
    st.markdown('<div class="utility-buttons">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("📞 Help", key="help_button", use_container_width=True):
            st.session_state.show_support = True
            st.rerun()
            
    with col2:
        warning_placeholder = st.empty()
        
        if st.button("🚪 Logout", key="logout_button", use_container_width=True):
            warning_placeholder.warning("⚠️ Logging out in 3 seconds...")
            time.sleep(1)
            warning_placeholder.warning("⚠️ Logging out in 2 seconds...")
            time.sleep(1)
            warning_placeholder.warning("⚠️ Logging out in 1 second...")
            time.sleep(1)
            warning_placeholder.empty()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

def route_to_platform(platform_name, username):
    """Route to appropriate platform page"""
    # Check if support form should be shown
    if 'show_support' in st.session_state and st.session_state.show_support:
        show_support_form()
        if st.button("← Back to Platform"):
            st.session_state.show_support = False
            st.rerun()
        return
    
    # Route to appropriate platform
    if platform_name == 'PhonePe':
        show_phonepe_page(username)
    elif platform_name == 'Paytm':
        show_paytm_page(username)
    elif platform_name == 'SuperMoney':
        show_supermoney_page(username)
    elif platform_name:
        # Show coming soon message for other platforms
        st.markdown(f"""
            <h3 style='
                font-size: 1.5rem;
                color: #FFFFFF;
                margin-bottom: 1rem;
                font-weight: 700;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
            '>{platform_name} Statement Analyzer</h3>
            
            <div style='
                font-size: 1rem;
                color: #FFFFFF;
                margin-bottom: 1rem;
                line-height: 1.4;
                opacity: 0.8;
            '>
                🚧 Coming Soon! 🚧<br>
                We're working on adding support for {platform_name}!<br><br>
                Features in development:
                <ul>
                    <li>Statement parsing for {platform_name} format</li>
                    <li>Custom analytics for {platform_name} transactions</li>
                    <li>Specialized insights and recommendations</li>
                </ul>
                <br>
                For now, please try our PhonePe, Paytm, or SuperMoney statement analyzer.
            </div>
        """, unsafe_allow_html=True)
    
    # Show platform grid at bottom
    show_platform_grid() 