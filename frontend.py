import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Configuration ---
st.set_page_config(
    page_title="Quant Dashboard",
    page_icon="💹",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

# --- Helper Functions to Fetch Data from API ---

def fetch_data(endpoint):
    """Generic function to fetch data from the API."""
    try:
        response = requests.get(f"{API_URL}/{endpoint}")
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {e}")
        return None

def format_market_cap(value):
    """Formats a large number into a readable string (e.g., 2.5T, 150.3B)."""
    if value is None:
        return "N/A"
    if value >= 1e12:
        return f"${value/1e12:.2f}T"
    if value >= 1e9:
        return f"${value/1e9:.2f}B"
    if value >= 1e6:
        return f"${value/1e6:.2f}M"
    return f"${value}"

# --- UI Components ---

st.title("💹 Quantitative Finance Dashboard")

ticker = st.text_input("Enter a stock ticker (e.g., AAPL, GOOGL, MSFT)", "AAPL").upper()

st.sidebar.header("Analysis Options")
analysis_type = st.sidebar.radio(
    "Choose an analysis:",
    (
        "Company Information",
        "Historical Price",
        "Simple Moving Average (SMA)",
        "Bollinger Bands (BBands)",
        "Moving Average Convergence Divergence (MACD)",
        "Relative Strength Index (RSI)"
    )
)

# --- Main Content Area ---

if ticker:
    # --- Company Information ---
    if analysis_type == "Company Information":
        st.header(f"Company Information: {ticker}")
        data = fetch_data(f"stocks/{ticker}/info")
        if data:
            info = data.get("info", {})
            st.subheader(info.get('longName', 'N/A'))
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Sector", info.get('sector', 'N/A'))
            col2.metric("Industry", info.get('industry', 'N/A'))
            col3.metric("Market Cap", format_market_cap(info.get('marketCap')))

            with st.expander("Business Summary"):
                st.write(info.get('longBusinessSummary', 'No summary available.'))

    # --- Historical Price ---
    elif analysis_type == "Historical Price":
        st.header(f"Historical Price Chart: {ticker}")
        history_data = fetch_data(f"stocks/{ticker}/history")
        if history_data:
            df = pd.DataFrame(history_data['history'])
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close']
            )])
            fig.update_layout(title=f'{ticker} Candlestick Chart', xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("View Raw Data"):
                st.dataframe(df)

    # --- Simple Moving Average (SMA) ---
    elif analysis_type == "Simple Moving Average (SMA)":
        st.header(f"Simple Moving Average (SMA): {ticker}")
        window = st.sidebar.slider("SMA Window", min_value=5, max_value=200, value=20, step=5)
        
        history_data = fetch_data(f"stocks/{ticker}/history")
        sma_data = fetch_data(f"technicals/{ticker}/sma?window={window}")
        
        if history_data and sma_data:
            df_hist = pd.DataFrame(history_data['history'])
            df_hist['Date'] = pd.to_datetime(df_hist['Date'])
            
            df_sma = pd.Series(sma_data['sma']).reset_index()
            df_sma.columns = ['Date', 'SMA']
            df_sma['Date'] = pd.to_datetime(df_sma['Date'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_hist['Date'], y=df_hist['Close'], mode='lines', name='Close Price'))
            fig.add_trace(go.Scatter(x=df_sma['Date'], y=df_sma['SMA'], mode='lines', name=f'{window}-Day SMA'))
            fig.update_layout(title=f'{ticker} Price with {window}-Day SMA')
            st.plotly_chart(fig, use_container_width=True)

    # --- Bollinger Bands (BBands) ---
    elif analysis_type == "Bollinger Bands (BBands)":
        st.header(f"Bollinger Bands: {ticker}")
        window = st.sidebar.slider("Window", min_value=5, max_value=50, value=20, step=1)
        num_std = st.sidebar.slider("Standard Deviations", min_value=1, max_value=4, value=2, step=1)

        history_data = fetch_data(f"stocks/{ticker}/history")
        bbands_data = fetch_data(f"technicals/{ticker}/bbands?window={window}&num_std={num_std}")

        if history_data and bbands_data:
            df_hist = pd.DataFrame(history_data['history'])
            df_hist['Date'] = pd.to_datetime(df_hist['Date'])

            df_bbands = pd.DataFrame.from_dict(bbands_data['bands'], orient='index')
            df_bbands.index = pd.to_datetime(df_bbands.index)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_hist['Date'], y=df_hist['Close'], mode='lines', name='Close Price', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=df_bbands.index, y=df_bbands['Upper_Band'], mode='lines', name='Upper Band', line=dict(width=0.5, color='gray')))
            fig.add_trace(go.Scatter(x=df_bbands.index, y=df_bbands['Lower_Band'], mode='lines', name='Lower Band', line=dict(width=0.5, color='gray'), fill='tonexty', fillcolor='rgba(128,128,128,0.2)'))
            fig.add_trace(go.Scatter(x=df_bbands.index, y=df_bbands['Middle_Band'], mode='lines', name='Middle Band (SMA)', line=dict(dash='dash', color='orange')))
            fig.update_layout(title=f'{ticker} Bollinger Bands')
            st.plotly_chart(fig, use_container_width=True)

    # --- Moving Average Convergence Divergence (MACD) ---
    elif analysis_type == "Moving Average Convergence Divergence (MACD)":
        st.header(f"MACD: {ticker}")
        fast = st.sidebar.slider("Fast Period", 5, 50, 12, 1)
        slow = st.sidebar.slider("Slow Period", 10, 100, 26, 1)
        signal = st.sidebar.slider("Signal Period", 1, 50, 9, 1)
        
        history_data = fetch_data(f"stocks/{ticker}/history")
        macd_data = fetch_data(f"technicals/{ticker}/macd?fast={fast}&slow={slow}&signal={signal}")

        if history_data and macd_data:
            df_hist = pd.DataFrame(history_data['history'])
            df_hist['Date'] = pd.to_datetime(df_hist['Date'])
            
            df_macd = pd.DataFrame.from_dict(macd_data['macd'], orient='index')
            df_macd.index = pd.to_datetime(df_macd.index)

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
            # Price Chart
            fig.add_trace(go.Scatter(x=df_hist['Date'], y=df_hist['Close'], mode='lines', name='Close Price'), row=1, col=1)
            # MACD Chart
            fig.add_trace(go.Scatter(x=df_macd.index, y=df_macd['MACD_Line'], mode='lines', name='MACD Line'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df_macd.index, y=df_macd['Signal_Line'], mode='lines', name='Signal Line'), row=2, col=1)
            fig.add_trace(go.Bar(x=df_macd.index, y=df_macd['Histogram'], name='Histogram'), row=2, col=1)
            fig.update_layout(title=f'{ticker} Price and MACD', yaxis2_title='MACD')
            st.plotly_chart(fig, use_container_width=True)

    # --- Relative Strength Index (RSI) ---
    elif analysis_type == "Relative Strength Index (RSI)":
        st.header(f"Relative Strength Index (RSI): {ticker}")
        window = st.sidebar.slider("RSI Window", min_value=5, max_value=50, value=14, step=1)
        
        history_data = fetch_data(f"stocks/{ticker}/history")
        rsi_data = fetch_data(f"technicals/{ticker}/rsi?window={window}")

        if history_data and rsi_data:
            df_hist = pd.DataFrame(history_data['history'])
            df_hist['Date'] = pd.to_datetime(df_hist['Date'])
            
            df_rsi = pd.Series(rsi_data['rsi']).reset_index()
            df_rsi.columns = ['Date', 'RSI']
            df_rsi['Date'] = pd.to_datetime(df_rsi['Date'])

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
            # Price Chart
            fig.add_trace(go.Scatter(x=df_hist['Date'], y=df_hist['Close'], mode='lines', name='Close Price'), row=1, col=1)
            # RSI Chart
            fig.add_trace(go.Scatter(x=df_rsi['Date'], y=df_rsi['RSI'], mode='lines', name='RSI'), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            fig.update_layout(title=f'{ticker} Price and RSI', yaxis2_title='RSI')
            fig.update_yaxes(range=[0, 100], row=2, col=1)
            st.plotly_chart(fig, use_container_width=True)
