import streamlit as st

class PlatformSelector:
    def __init__(self):
        self.platforms = {
            'PhonePe': '📱',
            'Google Pay': '💳',
            'Paytm': '💰',
            'SuperMoney': '💸',
            'NAVI': '🏦',
            'Amazon Pay': '🛒',
            'WhatsApp Pay': '💬',
            'BHIM UPI': '🇮🇳',
            'Other': '🔄'
        }

    def show_platform_selector(self):
        st.header("Select Your Payment Platform")
        st.markdown("""
        Please select the platform you use for digital payments. 
        This helps us better analyze your transaction statement.
        """)

        # Create a radio button for platform selection
        selected_platform = st.radio(
            "Choose your payment platform:",
            options=list(self.platforms.keys()),
            format_func=lambda x: f"{self.platforms[x]} {x}",
            horizontal=True
        )

        # Store the selection in session state
        if selected_platform:
            # Show platform-specific message
            st.success(f"Selected platform: {self.platforms[selected_platform]} {selected_platform}")
            
            # Show platform-specific instructions
            self.show_platform_instructions(selected_platform)
            
            # Add continue button
            if st.button("Continue with " + selected_platform):
                st.session_state.selected_platform = selected_platform
                st.rerun()
            
            return selected_platform
        return None

    def show_platform_instructions(self, platform):
        instructions = {
            'PhonePe': """
            ### PhonePe Statement Instructions:
            1. Open PhonePe app
            2. Go to Profile → Statements
            3. Select date range
            4. Download PDF statement
            5. Upload the statement here
            """,
            'Google Pay': """
            ### Google Pay Statement Instructions:
            1. Open Google Pay
            2. Go to Profile → Payments
            3. Tap on Download Statement
            4. Choose date range
            5. Upload the PDF here
            """,
            'Paytm': """
            ### Paytm Statement Instructions:
            1. Login to Paytm
            2. Go to Passbook
            3. Select Statement Download
            4. Choose period
            5. Upload the generated PDF
            """,
            'SuperMoney': """
            ### SuperMoney Statement Instructions:
            1. Login to SuperMoney
            2. Navigate to Transactions
            3. Click on Download Statement
            4. Select date range
            5. Upload the PDF here
            """,
            'NAVI': """
            ### NAVI Statement Instructions:
            1. Open NAVI app
            2. Go to Transactions
            3. Click on Download
            4. Select statement period
            5. Upload the PDF file
            """,
            'Amazon Pay': """
            ### Amazon Pay Statement Instructions:
            1. Login to Amazon Pay
            2. Go to Transaction History
            3. Click Download Statement
            4. Choose time period
            5. Upload the statement here
            """,
            'WhatsApp Pay': """
            ### WhatsApp Pay Statement Instructions:
            1. Open WhatsApp
            2. Go to Payments
            3. Click on History
            4. Download statement
            5. Upload the PDF here
            """,
            'BHIM UPI': """
            ### BHIM UPI Statement Instructions:
            1. Open BHIM app
            2. Go to Transaction History
            3. Select Download Statement
            4. Choose date range
            5. Upload the PDF file
            """,
            'Other': """
            ### Other Platform Instructions:
            1. Download your transaction statement in PDF format
            2. Ensure it contains:
               - Transaction dates
               - Amount details
               - Transaction types (Credit/Debit)
            3. Upload the PDF here
            """
        }
        
        st.markdown(instructions.get(platform, "Please select a platform for instructions."))

def show_platform_selector():
    """Show platform selection dropdown"""
    platforms = [
        "Select Platform",
        "PhonePe",
        "Paytm",
        "SuperMoney",  # Added SuperMoney
        "Google Pay",
        "Amazon Pay",
        "BHIM"
    ]
    
    # Initialize platform selection in session state if not exists
    if 'selected_platform' not in st.session_state:
        st.session_state.selected_platform = platforms[0]
    
    # Platform selector in sidebar
    selected = st.sidebar.selectbox(
        "Select Payment Platform",
        platforms,
        index=platforms.index(st.session_state.selected_platform)
    )
    
    # Update session state if changed
    if selected != st.session_state.selected_platform:
        st.session_state.selected_platform = selected
        st.rerun()

def check_platform_selected():
    """Check if a platform is selected"""
    if 'selected_platform' not in st.session_state or st.session_state.selected_platform == "Select Platform":
        st.warning("⚠️ Please select a payment platform from the sidebar")
        return False
    return True 