import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

print(os.getcwd())  # Add this line temporarily to your support.py to see the current working directory

def show_support_form():
    """Show the support form"""
    st.title("📞 Support")
    st.markdown("""
    Need help? Fill out this form and we'll get back to you as soon as possible.
    """)
    
    with st.form("support_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        issue = st.text_area("Describe your issue")
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            if name and email and issue:
                # Here you would typically send this to your support system
                st.success("Support request submitted! We'll get back to you soon.")
                time.sleep(2)
                st.session_state.show_support = False
                st.rerun()  # Changed from st.experimental_rerun()
            else:
                st.error("Please fill out all fields")

def show_support_form_old():
    st.header("📞 Contact Support")
    
    # Initialize form_submitted in session state if it doesn't exist
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    
    with st.form("support_form", clear_on_submit=True):
        # Get user details
        name = st.text_input("Your Name*")
        email = st.text_input("Email Address*")
        phone = st.text_input("Phone Number")
        platform = st.selectbox(
            "Related Platform*",
            ["PhonePe", "Google Pay", "Paytm", "SuperMoney", "NAVI", 
             "Amazon Pay", "WhatsApp Pay", "BHIM UPI", "Other"]
        )
        issue_type = st.selectbox(
            "Type of Issue*",
            ["Technical Problem", "Feature Request", "Statement Upload Issue", 
             "Analysis Error", "General Question", "Other"]
        )
        description = st.text_area("Describe your issue/question*", height=150)
        
        # Submit button
        submitted = st.form_submit_button("Submit Support Request")
        
        if submitted:
            if name and email and description:  # Required fields
                try:
                    # Create support request entry
                    support_data = {
                        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Name': name,
                        'Email': email,
                        'Phone': phone,
                        'Platform': platform,
                        'Issue_Type': issue_type,
                        'Description': description,
                        'Status': 'New'
                    }
                    
                    # Load existing or create new support sheet
                    filename = 'support_requests.xlsx'
                    if os.path.exists(filename):
                        df = pd.read_excel(filename)
                        df = pd.concat([df, pd.DataFrame([support_data])], ignore_index=True)
                    else:
                        df = pd.DataFrame([support_data])
                    
                    # Save to Excel
                    df.to_excel(filename, index=False)
                    
                    # Show success message with progress bar
                    success_message = st.success("""
                    Thank you for contacting support! 
                    We have received your request and will get back to you soon.
                    """)
                    
                    # Add a progress bar
                    progress_bar = st.progress(0)
                    for i in range(100):
                        # Update progress bar
                        progress_bar.progress(i + 1)
                        time.sleep(0.01)  # Reduced sleep time for better UX
                    
                    # Remove success message and progress bar after 2 seconds
                    time.sleep(2)
                    success_message.empty()
                    progress_bar.empty()
                    
                    # Return to platform
                    st.session_state.show_support = False
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error submitting support request: {str(e)}")
                    # Log the error for debugging
                    print(f"Support form error: {str(e)}")
            else:
                st.error("Please fill in all required fields (*)")
    
    # If form was just submitted, clear the submitted flag
    if st.session_state.form_submitted:
        st.session_state.form_submitted = False 