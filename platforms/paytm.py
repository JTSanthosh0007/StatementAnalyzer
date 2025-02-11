import streamlit as st
from statement_parser import StatementParser
import plotly.express as px
import plotly.graph_objects as go

def show_paytm_page(username):
    st.markdown(f"""
        <h3 style='
            font-size: 1.5rem;
            color: #FFFFFF;
            margin-bottom: 1rem;
            font-weight: 700;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        '>💰 <span style='color: #FFFFFF;'>Paytm Statement Analyzer</span> - Welcome <span style='color: #FFFFFF;'>{username}</span>!</h3>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='
            font-size: 1rem;
            color: #FFFFFF;
            margin-bottom: 1rem;
            line-height: 1.4;
            opacity: 0.8;
        '>
            Analyze your Paytm statements securely and get instant insights.<br>
            Upload your Paytm transaction statement in PDF format.
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your Paytm statement (PDF)", 
        type=["pdf"],
        help="Your file is processed securely and never stored"
    )

    if uploaded_file:
        with st.spinner("Analyzing your statement..."):
            parser = StatementParser(uploaded_file)
            df = parser.parse()
            
            # Calculate net flow
            net_flow = df['amount'].sum()
            
            # Show basic stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Credits", f"₹{df[df['amount'] > 0]['amount'].sum():,.2f}")
            with col2:
                st.metric("Total Debits", f"₹{abs(df[df['amount'] < 0]['amount'].sum()):,.2f}")
            with col3:
                st.metric("Net Flow", f"₹{net_flow:,.2f}")
            
            # Show transactions
            st.subheader("📊 Transaction History")
            st.dataframe(df)
            
            # Add visualizations
            line_fig, pie_fig = parser.generate_spending_chart(df)

            if line_fig is not None or pie_fig is not None:
                st.subheader("📈 Spending Analysis")
                col1, col2 = st.columns(2)
                
                with col1:
                    if line_fig is not None:
                        st.plotly_chart(line_fig, use_container_width=True)
                    else:
                        st.info("Monthly spending trend not available.")
                        
                with col2:
                    if pie_fig is not None:
                        st.plotly_chart(pie_fig, use_container_width=True)
                    else:
                        st.info("Category distribution not available.")
            else:
                st.info("Spending analysis is not available for this statement.")

            # Show advanced insights
            show_spending_insights(df)
            
            # Show smart recommendations
            st.markdown("""
                <h3 style='color: #FFFFFF; font-size: 1.3rem; margin-top: 2rem;'>
                    🤖 AI-Powered Insights
                </h3>
            """, unsafe_allow_html=True)
            
            # Show transaction patterns
            st.markdown("### 📈 Transaction Patterns")
            show_transaction_patterns(df)
            
            # Show category analysis
            st.markdown("### 🎯 Category Analysis")
            show_category_analysis(df)

def show_spending_insights(df):
    """Show advanced spending insights"""
    st.markdown("""
        <h3 style='color: #FFFFFF; font-size: 1.3rem; margin-top: 2rem;'>
            💡 Smart Spending Insights
        </h3>
    """, unsafe_allow_html=True)
    
    # Monthly trends
    monthly_spending = df[df['amount'] < 0].groupby(
        df['date'].dt.strftime('%B %Y')
    )['amount'].sum().abs()
    
    # Category breakdown
    category_spending = df[df['amount'] < 0].groupby('category')['amount'].agg(['sum', 'count'])
    
    # Top merchants
    top_merchants = df[df['amount'] < 0].groupby('description')['amount'].sum().nlargest(5)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly trend chart
        fig = go.Figure()
        fig.add_trace(go.Line(
            x=monthly_spending.index,
            y=monthly_spending.values,
            mode='lines+markers',
            name='Monthly Spending'
        ))
        fig.update_layout(
            title='Monthly Spending Trend',
            xaxis_title='Month',
            yaxis_title='Amount (₹)',
            template='plotly_dark'
        )
        st.plotly_chart(fig)
        
    with col2:
        # Category distribution
        fig = px.treemap(
            category_spending.reset_index(),
            path=['category'],
            values='sum',
            title='Spending by Category'
        )
        st.plotly_chart(fig)
    
    # Spending recommendations
    st.markdown("""
        <h4 style='color: #FFFFFF; font-size: 1.1rem;'>
            🎯 Personalized Recommendations
        </h4>
    """, unsafe_allow_html=True)
    
    recommendations = generate_recommendations(df)
    for rec in recommendations:
        st.info(rec)

def generate_recommendations(df):
    """Generate smart spending recommendations"""
    recommendations = []
    
    # Analyze spending patterns
    monthly_spending = df[df['amount'] < 0]['amount'].sum() / df['date'].nunique() * 30
    high_spend_categories = df[df['amount'] < 0].groupby('category')['amount'].sum().nlargest(3)
    recurring_payments = df[df['amount'] < 0].groupby('description')['amount'].count()
    
    # Generate insights
    if monthly_spending > 50000:
        recommendations.append("💰 Your monthly spending is high. Consider setting a budget for non-essential expenses.")
    
    for cat, amount in high_spend_categories.items():
        recommendations.append(f"📊 {cat} is your top spending category (₹{abs(amount):,.2f}). Look for ways to optimize these expenses.")
    
    if len(recurring_payments[recurring_payments > 2]) > 0:
        recommendations.append("🔄 You have several recurring payments. Review your subscriptions and memberships.")
    
    return recommendations 