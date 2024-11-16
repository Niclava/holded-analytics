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
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Holded Sales Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .css-1v0mbdj.e115fcil1 {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

class HoldedAnalytics:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.holded.com/api/v1"
        self.headers = {
            "key": self.api_key,
            "Content-Type": "application/json"
        }

    def test_connection(self):
        """Test if the API key is valid"""
        try:
            response = requests.get(
                f"{self.base_url}/invoices/sales",
                headers=self.headers,
                params={"limit": 1}
            )
            return response.status_code == 200
        except:
            return False

    def get_sales_data(self, start_date, end_date):
        """Fetch sales data safely"""
        try:
            response = requests.get(
                f"{self.base_url}/invoices/sales",
                headers=self.headers,
                params={
                    "from": start_date,
                    "to": end_date
                }
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Error fetching data: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            return None

def main():
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.api_key = None

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
        
        st.markdown("""
        ### Need Help?
        - To find your API key, log into Holded and go to Settings > API
        - For support, contact your system administrator
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
        try:
            # Convert to DataFrame
            df = pd.DataFrame(sales_data)
            
            # Dashboard tabs
            tab1, tab2, tab3 = st.tabs([
                "📈 Sales Overview",
                "🔍 Product Analysis",
                "🎯 Forecasting"
            ])
            
            with tab1:
                st.subheader("Sales Overview")
                
                # Key metrics
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                with metrics_col1:
                    total_sales = df['total'].sum() if 'total' in df.columns else 0
                    st.metric(
                        "Total Sales",
                        f"${total_sales:,.2f}"
                    )
                with metrics_col2:
                    avg_order = df['total'].mean() if 'total' in df.columns else 0
                    st.metric(
                        "Average Order Value",
                        f"${avg_order:,.2f}"
                    )
                with metrics_col3:
                    st.metric(
                        "Number of Orders",
                        len(df)
                    )
                
                # Sales trend
                if 'date' in df.columns and 'total' in df.columns:
                    daily_sales = df.groupby(pd.to_datetime(df['date']).dt.date)['total'].sum()
                    fig = px.line(
                        daily_sales,
                        title="Daily Sales Trend",
                        labels={"value": "Sales ($)", "date": "Date"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Required columns not found in the data")

            with tab2:
                st.subheader("Product Analysis")
                
                if 'productId' in df.columns:
                    # Product selector
                    products = df['productId'].unique()
                    selected_product = st.selectbox(
                        "Select Product",
                        products
                    )
                    
                    # Product metrics
                    product_data = df[df['productId'] == selected_product]
                    
                    prod_col1, prod_col2 = st.columns(2)
                    with prod_col1:
                        st.metric(
                            "Product Total Sales",
                            f"${product_data['total'].sum():,.2f}"
                        )
                    with prod_col2:
                        if 'quantity' in product_data.columns:
                            st.metric(
                                "Units Sold",
                                product_data['quantity'].sum()
                            )
                    
                    # Product sales trend
                    if 'date' in product_data.columns and 'quantity' in product_data.columns:
                        product_daily = product_data.groupby(
                            pd.to_datetime(product_data['date']).dt.date
                        )['quantity'].sum()
                        
                        fig = px.line(
                            product_daily,
                            title=f"Daily Sales Trend - {selected_product}",
                            labels={"value": "Units Sold", "date": "Date"}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Product information not found in the data")

            with tab3:
                st.subheader("Sales Forecasting")
                
                if 'date' in df.columns and 'quantity' in df.columns:
                    # Forecast period selector
                    forecast_periods = st.slider(
                        "Forecast Periods (months)",
                        min_value=1,
                        max_value=12,
                        value=3
                    )
                    
                    if st.button("Generate Forecast"):
                        with st.spinner("Generating forecast..."):
                            try:
                                # Prepare data for forecasting
                                monthly_sales = df.groupby(
                                    pd.to_datetime(df['date']).dt.to_period('M')
                                )['quantity'].sum()
                                
                                if len(monthly_sales) > 12:  # Need enough data for seasonal model
                                    # Fit SARIMA model
                                    model = SARIMAX(
                                        monthly_sales,
                                        order=(1, 1, 1),
                                        seasonal_order=(1, 1, 1, 12)
                                    )
                                    results = model.fit(disp=False)
                                    
                                    # Generate forecast
                                    forecast = results.forecast(forecast_periods)
                                    
                                    # Plot results
                                    fig = go.Figure()
                                    
                                    # Historical data
                                    fig.add_trace(go.Scatter(
                                        x=monthly_sales.index.astype(str),
                                        y=monthly_sales.values,
                                        name="Historical",
                                        line=dict(color="blue")
                                    ))
                                    
                                    # Forecast
                                    fig.add_trace(go.Scatter(
                                        x=forecast.index.astype(str),
                                        y=forecast.values,
                                        name="Forecast",
                                        line=dict(color="red", dash="dash")
                                    ))
                                    
                                    fig.update_layout(
                                        title="Sales Forecast",
                                        xaxis_title="Date",
                                        yaxis_title="Units",
                                        hovermode="x unified"
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Download forecast
                                    forecast_df = pd.DataFrame({
                                        "Date": forecast.index.astype(str),
                                        "Predicted_Sales": forecast.values
                                    })
                                    
                                    st.download_button(
                                        label="Download Forecast",
                                        data=forecast_df.to_csv(index=False),
                                        file_name="sales_forecast.csv",
                                        mime="text/csv"
                                    )
                                else:
                                    st.warning("Not enough historical data for seasonal forecasting. Need at least 12 months of data.")
                            except Exception as e:
                                st.error(f"Error generating forecast: {str(e)}")
                else:
                    st.warning("Required data for forecasting not found")

        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            st.write("Please check the structure of your Holded data")
    else:
        st.warning("No data available for the selected date range")

if __name__ == "__main__":
    main()
