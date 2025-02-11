import streamlit as st
from statement_parser import StatementParser
import time
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def show_phonepe_page(username):
    # Add mobile-friendly CSS
    st.markdown("""
        <style>
        /* Mobile-friendly styles */
        @media (max-width: 768px) {
            .stApp {
                margin: 0;
                padding: 0.5rem;
            }
            
            /* Make columns stack on mobile */
            [data-testid="column"] {
                width: 100% !important;
                margin-bottom: 1rem;
            }
            
            /* Adjust chart sizes */
            .js-plotly-plot {
                height: 300px !important;
            }
            
            /* Make metrics more readable */
            [data-testid="metric-container"] {
                width: 100% !important;
                padding: 0.5rem !important;
            }
            
            /* Adjust dataframe width */
            .stDataFrame {
                width: 100% !important;
                overflow-x: auto !important;
            }
            
            /* Make text more readable on mobile */
            .small-text {
                font-size: 0.9rem !important;
            }
            
            /* Adjust spacing */
            .block-container {
                padding-top: 1rem !important;
                padding-bottom: 1rem !important;
            }
            
            /* Make treemap and charts responsive */
            .plotly-graph-div {
                width: 100% !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <h3 style='
            font-size: 1.5rem;
            color: #FFFFFF;
            margin-bottom: 1rem;
            font-weight: 700;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        '>📱 <span style='color: #FFFFFF;'>PhonePe Statement Analyzer</span> - Welcome <span style='color: #FFFFFF;'>{username}</span>!</h3>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='
            font-size: 1rem;
            color: #FFFFFF;
            margin-bottom: 1rem;
            line-height: 1.4;
            opacity: 0.8;
        '>
            Analyze your PhonePe statements securely and get instant insights.<br>
            Upload your PhonePe transaction statement in PDF format.
        </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload your PhonePe statement (PDF)", 
        type=["pdf"],
        help="Your file is processed securely and never stored"
    )

    if uploaded_file:
        with st.spinner("Analyzing your statement..."):
            parser = StatementParser(uploaded_file)
            df = parser.parse()
            
            # Make metrics stack vertically on mobile
            st.markdown("""
                <div class="metrics-container">
            """, unsafe_allow_html=True)
            
            # Show basic stats in full width on mobile
            st.metric("Total Credits", f"₹{df[df['amount'] > 0]['amount'].sum():,.2f}")
            st.metric("Total Debits", f"₹{abs(df[df['amount'] < 0]['amount'].sum()):,.2f}")
            st.metric("Net Flow", f"₹{df['amount'].sum():,.2f}")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Show transactions with horizontal scroll on mobile
            st.subheader("📊 Transaction History")
            st.markdown("""
                <div style='overflow-x: auto;'>
            """, unsafe_allow_html=True)
            st.dataframe(df)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Make charts full width on mobile
            line_fig, pie_fig = parser.generate_spending_chart(df)
            if line_fig is not None:
                st.plotly_chart(line_fig, use_container_width=True)
            if pie_fig is not None:
                st.plotly_chart(pie_fig, use_container_width=True)
            
            # Show warning if net flow is negative
            if df['amount'].sum() < 0:
                # Create a placeholder for the warning
                warning_placeholder = st.empty()
                
                # Show the warning message
                warning_placeholder.markdown(
                    f"""
                    <div style="
                        background-color: #ffebee;
                        padding: 20px;
                        border-radius: 10px;
                        border-left: 5px solid #f44336;
                        margin: 10px 0px;
                        width: 50%;
                    ">
                        <h2 style="color: #d32f2f; margin:0;">⚠️ Warning: Net Loss Detected</h2>
                        <p style="color: #d32f2f; font-size: 16px; margin:10px 0;">
                            Your spending exceeds your income by <strong>₹{abs(df['amount'].sum()):,.2f}</strong>
                        </p>
                        <p style="color: #d32f2f; font-size: 14px; margin:0;">
                            Consider reviewing your expenses to maintain a healthy financial balance.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Wait for 3 seconds
                time.sleep(3)
                
                # Clear the warning
                warning_placeholder.empty()
            
            # Show advanced insights
            show_spending_insights(df)
            
            # Show smart recommendations
            st.markdown("""
                <h3 style='color: #FFFFFF; font-size: 1.3rem; margin-top: 2rem;'>
                    🤖 AI-Powered Insights
                </h3>
            """, unsafe_allow_html=True)
            
            # Show transaction patterns
            show_transaction_patterns(df)
            
            # Show category analysis
            show_category_analysis(df)

def show_spending_insights(df):
    """Show advanced spending insights with mobile-friendly layout"""
    st.markdown("""
        <h3 style='color: #FFFFFF; font-size: 1.3rem; margin-top: 2rem;'>
            💡 Smart Spending Insights
        </h3>
    """, unsafe_allow_html=True)
    
    # Check if DataFrame is empty or has no valid transactions
    if df.empty or 'amount' not in df.columns or 'date' not in df.columns:
        st.info("Please upload a valid statement to view spending insights.")
        return
    
    # Get spending transactions
    spending_df = df[df['amount'] < 0].copy()
    
    if spending_df.empty:
        st.info("No spending transactions found in the uploaded statement.")
        return
    
    try:
        # Monthly trends
        monthly_spending = spending_df.groupby(
            spending_df['date'].dt.strftime('%B %Y')
        )['amount'].sum().abs()
        
        if not monthly_spending.empty:
            # Category breakdown
            category_spending = spending_df.groupby('category')['amount'].agg(['sum', 'count'])
            
            # Make charts full width on mobile
            with st.container():
                # Monthly trend chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly_spending.index,
                    y=monthly_spending.values,
                    mode='lines+markers',
                    name='Monthly Spending',
                    line=dict(
                        width=2,
                        color='rgb(50, 171, 96)'
                    )
                ))
                fig.update_layout(
                    title='Monthly Spending Trend',
                    xaxis_title='Month',
                    yaxis_title='Amount (₹)',
                    template='plotly_dark',
                    height=300,  # Smaller height for mobile
                    margin=dict(l=10, r=10, t=30, b=10)  # Tighter margins
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Category distribution
                if not category_spending.empty:
                    fig = px.treemap(
                        category_spending.reset_index(),
                        path=['category'],
                        values='sum',
                        title='Spending by Category'
                    )
                    fig.update_layout(height=300)  # Smaller height for mobile
                    st.plotly_chart(fig, use_container_width=True)
            
            # Show merchant analysis only if description column exists and has data
            if 'description' in df.columns and not spending_df.empty:
                top_merchants = spending_df.groupby('description')['amount'].sum().nlargest(5)
                
                if not top_merchants.empty:
                    st.markdown("#### 🏪 Top Merchants")
                    for merchant, amount in top_merchants.items():
                        st.info(f"💳 {merchant}: ₹{abs(amount):,.2f}")
        
        # Generate recommendations only if we have spending data
        if not spending_df.empty:
            st.markdown("""
                <h4 style='color: #FFFFFF; font-size: 1.1rem;'>
                    🎯 Personalized Recommendations
                </h4>
            """, unsafe_allow_html=True)
            
            recommendations = generate_recommendations(spending_df)
            for rec in recommendations:
                st.info(rec)
                
    except Exception as e:
        st.info("Processing your transaction data. Please ensure the statement format is correct.")

def generate_recommendations(df):
    """Generate smart spending recommendations"""
    recommendations = []
    
    try:
        # Monthly spending analysis
        monthly_spending = df['amount'].sum() / df['date'].nunique() * 30
        
        # Category analysis
        high_spend_categories = df.groupby('category')['amount'].sum().nlargest(3)
        
        # Transaction size analysis
        large_transactions = df[df['amount'].abs() > 5000]
        
        # Time-based analysis
        daily_spending = df.groupby(df['date'].dt.day_name())['amount'].sum()
        
        # Generate insights
        if monthly_spending > 50000:
            recommendations.append("💰 Your monthly spending is high. Consider setting a budget for non-essential expenses.")
        
        if len(high_spend_categories) > 0:
            top_category = high_spend_categories.index[0]
            recommendations.append(f"📊 {top_category} is your top spending category (₹{abs(high_spend_categories.iloc[0]):,.2f}). Look for ways to optimize these expenses.")
        
        if len(large_transactions) > 0:
            recommendations.append(f"⚠️ You have {len(large_transactions)} large transactions (>₹5,000). Review these for potential savings.")
        
        if len(daily_spending) > 0:
            highest_spending_day = daily_spending.abs().idxmax()
            recommendations.append(f"📅 {highest_spending_day} shows highest spending. Plan your transactions on lower-spend days.")
        
        # Average transaction size
        avg_transaction = df['amount'].mean()
        if abs(avg_transaction) > 2000:
            recommendations.append(f"💳 Your average transaction size (₹{abs(avg_transaction):,.2f}) is high. Consider breaking down large purchases.")
        
        # Spending trend
        recent_spending = df.sort_values('date').tail(10)['amount'].sum()
        if abs(recent_spending) > monthly_spending/3:
            recommendations.append("📈 Your recent spending has increased. Monitor your expenses closely.")
        
        # Balance recommendation
        if df['amount'].sum() < 0:
            recommendations.append("🏦 Your account shows a net outflow. Consider ways to increase savings.")
            
    except Exception as e:
        recommendations.append("💡 Upload more transaction data to get personalized recommendations.")
    
    return recommendations

def show_transaction_patterns(df):
    """Show transaction patterns with mobile-friendly layout"""
    st.markdown("### 📈 Transaction Patterns")
    
    if 'amount' not in df.columns or 'date' not in df.columns:
        st.info("We need more transaction data to analyze patterns. Please ensure your statement includes complete details.")
        return
        
    try:
        # Daily transaction patterns
        daily_stats = df.groupby(df['date'].dt.day_name()).agg({
            'amount': ['count', 'mean']
        }).round(2)
        daily_stats.columns = ['Number of Transactions', 'Average Amount']
        
        # Time-based insights
        st.markdown("#### 📅 Day-wise Transaction Patterns")
        
        # Create a bar chart for daily patterns
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily_stats.index,
            y=daily_stats['Number of Transactions'],
            name='Number of Transactions',
            marker_color='rgba(50, 171, 96, 0.7)'
        ))
        
        fig.update_layout(
            title='Transaction Frequency by Day of Week',
            xaxis_title='Day of Week',
            yaxis_title='Number of Transactions',
            template='plotly_dark',
            showlegend=False,
            height=300,  # Smaller height for mobile
            margin=dict(l=10, r=10, t=30, b=10)  # Tighter margins
        )
        st.plotly_chart(fig, use_container_width=True)

        # Transaction size distribution
        st.markdown("#### 💰 Transaction Size Analysis")
        
        # Create transaction size categories
        df['transaction_size'] = pd.cut(
            df['amount'].abs(),
            bins=[0, 1000, 5000, 10000, float('inf')],
            labels=['Small (≤₹1,000)', 'Medium (₹1,001-₹5,000)', 'Large (₹5,001-₹10,000)', 'Very Large (>₹10,000)']
        )
        
        size_dist = df['transaction_size'].value_counts()
        
        # Create pie chart for transaction sizes
        fig = px.pie(
            values=size_dist.values,
            names=size_dist.index,
            title='Transaction Size Distribution'
        )
        fig.update_layout(height=300)  # Smaller height for mobile
        st.plotly_chart(fig, use_container_width=True)

        # Show key insights
        st.markdown("#### 🔍 Key Pattern Insights")
        
        # Busiest day
        busiest_day = daily_stats['Number of Transactions'].idxmax()
        st.info(f"📊 Your busiest transaction day is {busiest_day} with "
                f"{int(daily_stats.loc[busiest_day, 'Number of Transactions'])} transactions")
        
        # Most common transaction size
        common_size = size_dist.index[0]
        st.info(f"💳 Most of your transactions ({size_dist.iloc[0]} transactions) are in the {common_size} range")
        
        # Average transaction by day
        highest_avg_day = daily_stats['Average Amount'].abs().idxmax()
        st.info(f"💰 Your highest average transaction amount occurs on {highest_avg_day}s "
                f"(₹{abs(daily_stats.loc[highest_avg_day, 'Average Amount']):,.2f})")

    except Exception as e:
        st.info("We're analyzing your transaction patterns. Some visualizations might be temporarily unavailable.")

def show_category_analysis(df):
    """Show category analysis with mobile-friendly layout"""
    st.markdown("### 🎯 Category Analysis")
    
    if 'category' not in df.columns:
        st.info("We need category information to show this analysis. Please ensure your statement includes transaction categories.")
        return
        
    try:
        # Category-wise spending
        category_stats = df[df['amount'] < 0].groupby('category').agg({
            'amount': ['sum', 'count', 'mean']
        }).round(2)
        
        category_stats.columns = ['Total Amount', 'Number of Transactions', 'Average Transaction']
        category_stats['Total Amount'] = category_stats['Total Amount'].abs()
        category_stats['Average Transaction'] = category_stats['Average Transaction'].abs()
        
        # Sort by total amount
        category_stats = category_stats.sort_values('Total Amount', ascending=False)
        
        # Display category statistics
        st.markdown("#### Category-wise Spending Analysis")
        st.markdown("""
            <div style='overflow-x: auto;'>
        """, unsafe_allow_html=True)
        st.dataframe(category_stats.style.format({
            'Total Amount': '₹{:,.2f}',
            'Average Transaction': '₹{:,.2f}'
        }))
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Show insights
        st.markdown("#### 💡 Category Insights")
        
        # Most expensive category
        most_expensive = category_stats.index[0]
        st.info(f"📊 Your highest spending category is '{most_expensive}' "
                f"with ₹{category_stats.loc[most_expensive, 'Total Amount']:,.2f} "
                f"across {int(category_stats.loc[most_expensive, 'Number of Transactions'])} transactions.")
        
        # Highest average transaction
        highest_avg = category_stats['Average Transaction'].idxmax()
        st.info(f"💰 '{highest_avg}' has the highest average transaction amount "
                f"of ₹{category_stats.loc[highest_avg, 'Average Transaction']:,.2f}.")
        
        # Most frequent category
        most_frequent = category_stats['Number of Transactions'].idxmax()
        st.info(f"🔄 You made the most transactions in '{most_frequent}' "
                f"with {int(category_stats.loc[most_frequent, 'Number of Transactions'])} transactions.")
                
    except Exception as e:
        st.info("We're processing your category data. Some insights might be temporarily unavailable.") 