# app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
import json
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Holded Sales Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class HoldedAnalytics:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.holded.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",  # Changed to Bearer token
            "Content-Type": "application/json"
        }

    def test_connection(self):
        """Test if the API key is valid"""
        try:
            # Debug information
            st.sidebar.write("Testing connection...")
            
            response = requests.get(
                f"{self.base_url}/invoices",  # Changed endpoint
                headers=self.headers
            )
            
            # Debug information
            st.sidebar.write(f"Status Code: {response.status_code}")
            st.sidebar.write(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 401:
                st.error("Authentication failed. Please check your API key.")
                return False
                
            return response.status_code == 200
            
        except Exception as e:
            st.error(f"Connection test error: {str(e)}")
            return False

    def get_sales_data(self, start_date, end_date):
        """Fetch sales data safely"""
        try:
            # Debug information
            st.sidebar.write("Fetching sales data...")
            st.sidebar.write(f"Date range: {start_date} to {end_date}")
            
            # Format dates correctly
            start = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            
            response = requests.get(
                f"{self.base_url}/invoices",  # Changed endpoint
                headers=self.headers,
                params={
                    "dateFrom": start,
                    "dateTo": end
                }
            )
            
            # Debug information
            st.sidebar.write(f"API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Debug information
                    st.sidebar.write(f"Records found: {len(data) if isinstance(data, list) else 'Not a list'}")
                    return data
                except json.JSONDecodeError:
                    st.error("Invalid JSON response from API")
                    st.sidebar.write(f"Raw response: {response.text[:500]}...")  # Show first 500 chars
                    return None
            else:
                st.error(f"API Error: {response.status_code}")
                st.sidebar.write(f"Error response: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Data fetch error: {str(e)}")
            return None

def process_sales_data(data):
    """Process raw sales data into a DataFrame"""
    try:
        if not data or not isinstance(data, list):
            st.warning("No valid data to process")
            return None
            
        # Extract relevant fields
        processed_data = []
        for invoice in data:
            # Extract basic invoice info
            invoice_info = {
                'date': invoice.get('date'),
                'total': invoice.get('total', 0),
                'status': invoice.get('status'),
                'id': invoice.get('id')
            }
            
            # Extract line items
            items = invoice.get('items', [])
            for item in items:
                item_info = invoice_info.copy()
                item_info.update({
                    'productId': item.get('productId'),
                    'quantity': item.get('units', 0),
                    'item_total': item.get('subtotal', 0)
                })
                processed_data.append(item_info)
        
        df = pd.DataFrame(processed_data)
        
        # Convert date
        df['date'] = pd.to_datetime(df['date'])
        
        # Debug information
        st.sidebar.write(f"Processed data shape: {df.shape}")
        st.sidebar.write("Columns found:", df.columns.tolist())
        
        return df
        
    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        return None

def main():
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.api_key = None

    # Add debug mode toggle
    debug_mode = st.sidebar.checkbox("Debug Mode")

    # Logout handler
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.api_key = None
        st.rerun()

    # Authentication screen
    if not st.session_state.authenticated:
        st.title("👋 Welcome to Holded Sales Analytics")
        
        st.markdown("""
        ### Quick Start Guide
        1. Enter your Holded API key below
        2. Select your date range
        3. Explore your sales data with interactive visualizations
        4. Generate forecasts and recommendations
        
        > 🔒 Your API key is securely stored in your session and never saved permanently
        """)

        api_key = st.text_input("Enter your Holded API key", type="password")
        
        if st.button("Connect to Holded"):
            if api_key:
                analyzer = HoldedAnalytics(api_key)
                if analyzer.test_connection():
                    st.session_state.api_key = api_key
                    st.session_state.authenticated = True
                    st.success("Successfully connected to Holded!")
                    st.rerun()
                else:
                    st.error("Invalid API key or connection error")
            else:
                st.warning("Please enter your API key")
        
        # Show API key format hint
        st.info("""
        💡 Your API key should look like: 'xx-xxxxxxxxxxxxxxxxxxxxx'
        Find it in Holded under: Settings → Developer tools → API Keys
        """)
        
        return

    # Main application after authentication
    st.title("📊 Holded Sales Analytics Dashboard")
    
    # Initialize analyzer
    analyzer = HoldedAnalytics(st.session_state.api_key)
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=365)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )

    # Fetch data
    with st.spinner("Fetching your sales data..."):
        sales_data = analyzer.get_sales_data(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

    if sales_data:
        # Process data
        df = process_sales_data(sales_data)
        
        if df is not None and not df.empty:
            # Rest of your dashboard code...
            st.success("Data loaded successfully!")
            
            # Show raw data in debug mode
            if debug_mode:
                st.subheader("Raw Data Sample")
                st.write(df.head())
                st.write("Data Shape:", df.shape)
        else:
            st.warning("No data available for the selected date range")
    else:
        st.warning("No data available for the selected date range")

if __name__ == "__main__":
    main()
