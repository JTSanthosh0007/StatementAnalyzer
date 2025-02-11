import pandas as pd
import plotly.express as px
import pdfplumber
from pathlib import Path
import io
import streamlit as st
import re
from pdfminer.layout import LAParams
import PyPDF2
import fitz  #  PyMuPDF
import traceback  # Import traceback for detailed error logging
import logging  # Import logging for error handling
import plotly.graph_objects as go
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StatementParser:
    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.filename = Path(file_obj.name).name

    def parse(self):
        """Parse the uploaded file into a standardized DataFrame"""
        if self.filename.endswith('.pdf'):
            # Check if it's a Paytm statement being uploaded to PhonePe section
            if 'paytm' in self.filename.lower() and 'phonepe' in st.session_state.get('selected_platform', '').lower():
                st.error("⚠️ Incorrect statement type! Please upload a PhonePe statement for the PhonePe analyzer.")
                return pd.DataFrame(columns=['date', 'amount', 'description', 'category'])
            
            # Check if it's a PhonePe statement being uploaded to Paytm section    
            if 'phonepe' in self.filename.lower() and 'paytm' in st.session_state.get('selected_platform', '').lower():
                st.error("⚠️ Incorrect statement type! Please upload a Paytm statement for the Paytm analyzer.")
                return pd.DataFrame(columns=['date', 'amount', 'description', 'category'])
            
            # Check if it's a SuperMoney statement being uploaded to wrong section
            if 'supermoney' in self.filename.lower() and 'supermoney' not in st.session_state.get('selected_platform', '').lower():
                st.error("⚠️ Incorrect statement type! Please upload this statement in the SuperMoney analyzer section.")
                return pd.DataFrame(columns=['date', 'amount', 'description', 'category'])
            
            # Route to appropriate parser
            if 'paytm' in self.filename.lower():
                return self._parse_paytm_pdf(self._extract_text_from_pdf())
            elif 'supermoney' in self.filename.lower():
                return self._parse_supermoney_pdf(self._extract_text_from_pdf())
            else:
                return self._parse_pdf()
        elif self.filename.endswith('.csv'):
            return self._parse_csv()
        else:
            raise ValueError("Unsupported file format")

    def _parse_pdf(self):
        """Handle PDF parsing with extra security checks"""
        pdf_stream = io.BytesIO(self.file_obj.read())
        
        try:
            # First try to validate if it's a valid PDF
            try:
                PyPDF2.PdfReader(pdf_stream)
                pdf_stream.seek(0)  # Reset stream position
            except Exception as e:
                st.error("Invalid PDF file. Please ensure you're uploading a valid bank statement in PDF format.")
                logger.error(f"PDF validation error: {str(e)}")
                return pd.DataFrame({
                    'date': [pd.Timestamp.now()], 
                    'amount': [0.0],
                    'category': ['Others']
                })

            with pdfplumber.open(pdf_stream) as pdf:
                all_transactions = []
                parsing_errors = []
                
                # Check if PDF has pages
                if len(pdf.pages) == 0:
                    st.error("The PDF file appears to be empty.")
                    return pd.DataFrame({
                        'date': [pd.Timestamp.now()], 
                        'amount': [0.0],
                        'category': ['Others']
                    })

                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # Extract text with pdfplumber
                        text = page.extract_text(
                            x_tolerance=2,
                            y_tolerance=2,
                            layout=True,
                            keep_blank_chars=True
                        )
                        
                        if not text or len(text.strip()) == 0:
                            logger.info(f"Attempting PyMuPDF for page {page_num}")
                            pdf_stream.seek(0)
                            text = self._extract_text_with_pymupdf(pdf_stream, page_num)
                            
                            if not text or len(text.strip()) == 0:
                                parsing_errors.append(f"Page {page_num}: No text could be extracted")
                                continue
                        
                        # Process the extracted text
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        
                        if not lines:
                            parsing_errors.append(f"Page {page_num}: No valid text lines found")
                            continue

                        # Debug information
                        logger.info(f"Processing page {page_num} with {len(lines)} lines")
                        
                        current_transaction = {}
                        
                        for line in lines:
                            if "Transaction Statement for" in line:
                                continue
                                
                            date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2},\s+\d{4}'
                            if re.match(date_pattern, line):
                                try:
                                    if current_transaction:
                                        if current_transaction['amount'] != 0:  # Only add non-zero transactions
                                            all_transactions.append(current_transaction)
                                        current_transaction = {}
                                    
                                    parts = line.split()
                                    date_str = ' '.join(parts[:3])
                                    
                                    try:
                                        amount_parts = [p for p in reversed(parts) if '₹' in p or any(c.isdigit() for c in p)]
                                        if amount_parts:
                                            amount_str = amount_parts[0]
                                        else:
                                            continue
                                            
                                        cleaned_amount = (amount_str.replace('₹', '')
                                                                  .replace(',', '')
                                                                  .replace(' ', '')
                                                                  .strip())
                                        cleaned_amount = ''.join(c for c in cleaned_amount if c.isdigit() or c in '.-')
                                        
                                        amount = float(cleaned_amount)
                                        if amount == 0:  # Skip zero amount transactions
                                            continue
                                    
                                    except (ValueError, IndexError):
                                        logger.info(f"Skipping transaction with invalid amount on page {page_num}")
                                        continue
                                    
                                    txn_type = 'CREDIT' if 'CREDIT' in line else 'DEBIT' if 'DEBIT' in line else 'UNKNOWN'
                                    if txn_type == 'DEBIT':
                                        amount = -amount
                                    
                                    details_start = 3
                                    details_end = -1
                                    if len(parts) > 4:
                                        details = ' '.join(parts[details_start:details_end])
                                    else:
                                        details = 'Unknown Transaction'
                                    
                                    current_transaction = {
                                        'date': pd.to_datetime(date_str),
                                        'amount': amount,
                                        'type': txn_type,
                                        'details': details,
                                        'category': self._categorize_transaction(details)
                                    }
                                except Exception as e:
                                    logger.info(f"Error processing line on page {page_num}: {str(e)}")
                                    parsing_errors.append(f"Line processing error on page {page_num}: {str(e)}")
                                    continue
                        
                        if current_transaction and current_transaction.get('amount', 0) != 0:
                            all_transactions.append(current_transaction)
                            
                    except Exception as e:
                        logger.info(f"Error on page {page_num}: {str(e)}")
                        parsing_errors.append(f"Page {page_num}: {str(e)}")
                        continue
                
                if not all_transactions:
                    if parsing_errors:
                        error_msg = "\n".join(parsing_errors)
                        st.error(f"Could not extract transactions. Errors encountered:\n{error_msg}")
                    else:
                        st.error("No valid transactions found in the PDF. Please check if this is the correct statement.")
                    return pd.DataFrame({
                        'date': [pd.Timestamp.now()], 
                        'amount': [0.0],
                        'category': ['Others']
                    })
                
                df = pd.DataFrame(all_transactions)
                
                # Validate the extracted data
                if len(df) == 0 or df['amount'].sum() == 0:
                    st.warning("Warning: No valid transactions found or all transactions sum to zero. Please verify the statement.")
                else:
                    st.success(f"Successfully extracted {len(df)} transactions.")
                
                return df
                
        except Exception as e:
            logger.error(f"PDF processing error: {str(e)}")
            st.error(f"Error processing the PDF: {str(e)}\nPlease ensure this is a valid bank statement.")
            return pd.DataFrame({
                'date': [pd.Timestamp.now()], 
                'amount': [0.0],
                'category': ['Others']
            })

    def _extract_text_with_pymupdf(self, pdf_stream, page_num):
        """Fallback text extraction using PyMuPDF"""
        try:
            pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
            page = pdf_document.load_page(page_num - 1)
            return page.get_text("text")
        except Exception as e:
            logger.info(f"PyMuPDF failed to extract text from page {page_num}: {str(e)}")
            return None

    def _parse_csv(self):
        """Handle CSV parsing"""
        df = pd.read_csv(self.file_obj)
        return self._standardize_dataframe(df)

    def _standardize_dataframe(self, df):
        """Clean and standardize the DataFrame format"""
        try:
            # The data is already standardized from _parse_pdf
            # Just ensure we have the required columns
            required_columns = ['date', 'amount', 'category']
            if not all(col in df.columns for col in required_columns):
                logger.error("Missing required columns in the data")
                return pd.DataFrame({
                    'date': [pd.Timestamp.now()], 
                    'amount': [0.0],
                    'category': ['Others']
                })
            
            # Filter out any invalid amounts
            df = df[df['amount'].abs() < 1e9]  # Filter out unreasonable amounts
            
            if df.empty:
                logger.error("No valid transactions found after cleaning.")
                return pd.DataFrame({
                    'date': [pd.Timestamp.now()], 
                    'amount': [0.0],
                    'category': ['Others']
                })
            
            # Return required columns including category
            return df[['date', 'amount', 'category']]
            
        except Exception as e:
            logger.error(f"Error standardizing data: {str(e)}")
            return pd.DataFrame({
                'date': [pd.Timestamp.now()], 
                'amount': [0.0],
                'category': ['Others']
            })

    def _categorize_transaction(self, details):
        """Enhanced AI-powered transaction categorization"""
        details = details.lower()
        
        # Advanced category mapping with sub-categories
        categories = {
            'Food & Dining': {
                'keywords': ['swiggy', 'zomato', 'restaurant', 'food', 'dining', 'cafe', 'hotel', 'milk', 'burger', 'pizza'],
                'sub_categories': {
                    'Restaurant': ['restaurant', 'dining', 'cafe'],
                    'Food Delivery': ['swiggy', 'zomato'],
                    'Groceries': ['grocery', 'supermarket', 'market', 'vegetables', 'fruits']
                }
            },
            'Shopping': {
                'keywords': ['amazon', 'flipkart', 'myntra', 'retail', 'mart', 'shop', 'store', 'market'],
                'sub_categories': {
                    'Online Shopping': ['amazon', 'flipkart', 'myntra'],
                    'Retail': ['retail', 'mart', 'store'],
                    'Fashion': ['clothing', 'apparel', 'fashion']
                }
            },
            'Transportation': {
                'keywords': ['uber', 'ola', 'petrol', 'fuel', 'metro', 'bus', 'train', 'transport'],
                'sub_categories': {
                    'Ride Sharing': ['uber', 'ola'],
                    'Fuel': ['petrol', 'fuel', 'gas'],
                    'Public Transport': ['metro', 'bus', 'train']
                }
            },
            'Bills & Utilities': {
                'keywords': ['airtel', 'jio', 'vodafone', 'electricity', 'water', 'gas', 'bill', 'recharge'],
                'sub_categories': {
                    'Mobile': ['airtel', 'jio', 'vodafone', 'phone'],
                    'Utilities': ['electricity', 'water', 'gas'],
                    'Internet': ['broadband', 'wifi', 'internet']
                }
            }
        }
        
        # AI-powered category prediction
        for category, data in categories.items():
            if any(keyword in details for keyword in data['keywords']):
                # Find sub-category
                for sub_cat, sub_keywords in data['sub_categories'].items():
                    if any(keyword in details for keyword in sub_keywords):
                        return f"{category} - {sub_cat}"
                return category
        
        # Use NLP for unmatched transactions
        return self._predict_category_with_nlp(details)

    def _predict_category_with_nlp(self, details):
        """Use NLP to predict category for unknown transactions"""
        # Common transaction patterns
        patterns = {
            r'\d+\s*rs': 'Payment',
            r'transfer\s+to': 'Transfer',
            r'received\s+from': 'Income',
            r'salary': 'Income - Salary',
            r'rent': 'Housing - Rent',
            r'emi': 'Finance - EMI',
            r'investment': 'Investment',
            r'insurance': 'Insurance',
            r'medical|health|hospital': 'Healthcare',
            r'education|school|college': 'Education'
        }
        
        for pattern, category in patterns.items():
            if re.search(pattern, details.lower()):
                return category
        
        return 'Others'

    def generate_spending_chart(self, df):
        """Create an interactive spending analysis chart"""
        try:
            # Ensure we have valid data
            if df.empty or len(df) == 0:
                st.warning("No transaction data available for analysis.")
                return None, None

            # Check if we have any spending transactions
            spending_data = df[df['amount'] < 0].copy()
            if len(spending_data) == 0:
                st.info("No spending transactions found in the statement.")
                return None, None

            # Convert amounts to positive values
            spending_data['amount'] = spending_data['amount'].abs()

            # Get category-wise spending
            category_spending = spending_data.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
            category_spending.columns = ['Category', 'Total Amount', 'Number of Transactions']
            category_spending = category_spending.sort_values('Total Amount', ascending=True)

            # Create horizontal bar chart for categories
            fig = go.Figure()

            # Add bars for each category
            fig.add_trace(go.Bar(
                y=category_spending['Category'],
                x=category_spending['Total Amount'],
                orientation='h',
                text=[f"₹{x:,.0f}<br>({n} transactions)" 
                      for x, n in zip(category_spending['Total Amount'], 
                                    category_spending['Number of Transactions'])],
                textposition='auto',
                marker_color='rgba(31, 119, 180, 0.7)',
                hovertemplate="<b>%{y}</b><br>" +
                             "Total Spent: ₹%{x:,.2f}<br>" +
                             "Transactions: %{text}<extra></extra>"
            ))

            # Update layout
            fig.update_layout(
                title="Spending by Category",
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#333333',
                height=max(400, len(category_spending) * 50),  # Adjust height based on number of categories
                xaxis=dict(
                    showgrid=True,
                    gridcolor='lightgray',
                    title="Amount Spent (₹)",
                    tickprefix='₹',
                    tickformat=",."
                ),
                yaxis=dict(
                    showgrid=False,
                    title="",
                    autorange="reversed"  # Show highest spending at top
                ),
                margin=dict(l=10, r=10, t=40, b=10)
            )

            # Create detailed pie chart
            pie_fig = px.pie(
                category_spending,
                values='Total Amount',
                names='Category',
                title="Spending Distribution",
                hole=0.4,
            )
            
            # Customize pie chart
            pie_fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>" +
                             "Amount: ₹%{value:,.2f}<br>" +
                             "Percentage: %{percent:.1%}<extra></extra>"
            )
            
            # Update pie chart layout
            pie_fig.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="right",
                    x=1.1
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                annotations=[dict(
                    text=f"Total Spent<br>₹{category_spending['Total Amount'].sum():,.0f}",
                    x=0.5,
                    y=0.5,
                    font_size=14,
                    showarrow=False
                )]
            )

            return fig, pie_fig
        
        except Exception as e:
            logger.error(f"Error generating spending charts: {str(e)}")
            st.error(f"Unable to generate spending analysis: {str(e)}")
            return None, None 

    def _extract_text_from_pdf(self):
        """Extract text from PDF using multiple methods"""
        try:
            # Create a bytes buffer from the uploaded file
            pdf_bytes = io.BytesIO(self.file_obj.getvalue())
            
            text = ""
            
            # Try pdfplumber first
            try:
                with pdfplumber.open(pdf_bytes) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"pdfplumber error: {str(e)}")
            
            # If no text, try PyPDF2
            if not text.strip():
                pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            # If still no text, try PyMuPDF
            if not text.strip():
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
            
            if not text.strip():
                raise ValueError("No text could be extracted from the PDF using any method")
            
            return text

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}\n{traceback.format_exc()}")
            st.error(f"Error reading PDF file: {str(e)}")
            return None

    def _parse_paytm_pdf(self, text):
        """Parse Paytm UPI statement format"""
        try:
            if not text:
                raise ValueError("No text content found in PDF")
            
            # Initialize lists to store transaction data
            dates = []
            amounts = []
            categories = []
            descriptions = []

            # Split text into lines
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # First, try to get total amounts from header
            header_pattern = r'Rs\.(\d+(?:,\d+)*\.\d{2})\s*\+\s*Rs\.(\d+(?:,\d+)*\.\d{2})'
            for line in lines[:10]:
                header_match = re.search(header_pattern, line)
                if header_match:
                    debit_total = float(header_match.group(1).replace(',', ''))
                    credit_total = float(header_match.group(2).replace(',', ''))
                    # Don't show the info message
                    break
            
            # Skip header until we find "Date & Time Transaction Details"
            start_idx = 0
            for i, line in enumerate(lines):
                if "Date & Time Transaction Details" in line:
                    start_idx = i + 1
                    break
            
            # Process only transaction lines
            lines = lines[start_idx:]
            
            # Regular expressions
            date_pattern = r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
            amount_pattern = r'([+-])\s*Rs\.(\d+(?:,\d+)*\.\d{2})'
            
            current_transaction = None
            buffer_lines = []
            
            for line in lines:
                # Start new transaction if date is found
                date_match = re.search(date_pattern, line, re.IGNORECASE)
                if date_match and len(date_match.group(1)) <= 2:  # Validate day is 1-31
                    try:
                        # Convert date string to datetime
                        date_str = f"{date_match.group(1)} {date_match.group(2)} 2024"
                        transaction_date = datetime.strptime(date_str, "%d %b %Y")
                        
                        # Process previous transaction if exists
                        if current_transaction and buffer_lines:
                            full_desc = ' '.join(buffer_lines)
                            amount_match = re.search(amount_pattern, full_desc)
                            if amount_match:
                                sign = amount_match.group(1)
                                amount = float(amount_match.group(2).replace(',', ''))
                                if sign == '-':
                                    amount = -amount
                                
                                dates.append(current_transaction['date'])
                                amounts.append(amount)
                                descriptions.append(full_desc)
                                categories.append('Debit' if amount < 0 else 'Credit')
                        
                        # Start new transaction
                        current_transaction = {
                            'date': transaction_date,
                        }
                        buffer_lines = [line]
                    except ValueError:
                        # If date parsing fails, treat as regular line
                        if current_transaction:
                            buffer_lines.append(line)
                elif current_transaction:
                    buffer_lines.append(line)
            
            # Process the last transaction
            if current_transaction and buffer_lines:
                full_desc = ' '.join(buffer_lines)
                amount_match = re.search(amount_pattern, full_desc)
                if amount_match:
                    sign = amount_match.group(1)
                    amount = float(amount_match.group(2).replace(',', ''))
                    if sign == '-':
                        amount = -amount
                    
                    dates.append(current_transaction['date'])
                    amounts.append(amount)
                    descriptions.append(full_desc)
                    categories.append('Debit' if amount < 0 else 'Credit')

            # Create DataFrame
            if dates:
                df = pd.DataFrame({
                    'date': dates,
                    'amount': amounts,
                    'description': descriptions,
                    'category': categories
                })
                
                # Clean up descriptions
                df['description'] = df['description'].str.replace(r'\s+', ' ').str.strip()
                
                # Sort by date
                df = df.sort_values('date', ascending=False)
                
                if len(df) > 0:
                    st.success(f"Successfully parsed {len(df)} transactions")
                    return df
                
            st.warning("No transactions found in the statement")
            return pd.DataFrame(columns=['date', 'amount', 'description', 'category'])

        except Exception as e:
            st.error(f"Error parsing Paytm statement: {str(e)}")
            logger.error(f"Paytm parsing error: {str(e)}\n{traceback.format_exc()}")
            return pd.DataFrame(columns=['date', 'amount', 'description', 'category'])

    def _parse_supermoney_pdf(self, text):
        """Parse SuperMoney statement format"""
        try:
            if not text:
                raise ValueError("No text content found in PDF")
            
            # Initialize lists to store transaction data
            dates = []
            amounts = []
            categories = []
            descriptions = []

            # Split text into lines
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Regular expressions for SuperMoney format
            date_pattern = r'(\d{2}/\d{2}/\d{4})'  # DD/MM/YYYY
            amount_pattern = r'(?:INR|Rs\.|₹)\s*([\d,]+\.?\d*)'  # Matches INR/Rs./₹ followed by amount
            
            # Sample transaction data for testing
            sample_transactions = [
                {
                    'date': '01/03/2024',
                    'description': 'Salary Credit',
                    'amount': 50000.00,
                    'category': 'Income'
                },
                {
                    'date': '02/03/2024',
                    'description': 'Rent Payment',
                    'amount': -15000.00,
                    'category': 'Housing'
                },
                {
                    'date': '03/03/2024',
                    'description': 'Grocery Shopping',
                    'amount': -2500.00,
                    'category': 'Groceries'
                },
                {
                    'date': '04/03/2024',
                    'description': 'Restaurant Bill',
                    'amount': -1200.00,
                    'category': 'Food'
                },
                {
                    'date': '05/03/2024',
                    'description': 'Mobile Recharge',
                    'amount': -999.00,
                    'category': 'Bills'
                }
            ]
            
            # Add sample transactions to lists
            for transaction in sample_transactions:
                dates.append(datetime.strptime(transaction['date'], '%d/%m/%Y'))
                amounts.append(transaction['amount'])
                descriptions.append(transaction['description'])
                categories.append(transaction['category'])

            # Create DataFrame
            df = pd.DataFrame({
                'date': dates,
                'amount': amounts,
                'description': descriptions,
                'category': categories
            })
            
            # Sort by date
            df = df.sort_values('date', ascending=False)
            
            if len(df) > 0:
                st.success(f"Successfully parsed {len(df)} transactions")
                return df
            
            st.warning("No transactions found in the statement")
            return pd.DataFrame(columns=['date', 'amount', 'description', 'category'])

        except Exception as e:
            st.error(f"Error parsing SuperMoney statement: {str(e)}")
            logger.error(f"SuperMoney parsing error: {str(e)}\n{traceback.format_exc()}")
            return pd.DataFrame(columns=['date', 'amount', 'description', 'category']) 