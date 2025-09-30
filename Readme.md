# **Quantitative Finance Dashboard**

This project is a comprehensive quantitative finance dashboard built with a Python backend powered by **FastAPI** and a user-friendly frontend created with **Streamlit**. It allows users to fetch and visualize stock market data and common technical indicators for any given ticker symbol.

## **Features**

* **Company Information**: Get fundamental company data, including sector, industry, market cap, and business summary.  
* **Historical Price Data**: Visualize historical stock prices in an interactive candlestick chart.  
* **Technical Analysis Indicators**:  
  * Simple Moving Average (SMA)  
  * Bollinger Bands (BBands)  
  * Moving Average Convergence Divergence (MACD)  
  * Relative Strength Index (RSI)  
* **Interactive UI**: A clean, web-based interface built with Streamlit for easy interaction and analysis.  
* **RESTful API**: A robust backend API that serves all the financial data, which can be used independently.

## **Tech Stack**

* Backend: Python, FastAPI, uvicorn  
  \-- Frontend: Streamlit  
* **Data & Analysis**: pandas, numpy, yfinance  
* **Visualization**: plotly

## **Project Structure**

.  
├── main.py              \# The FastAPI backend application  
├── frontend.py         \# The Streamlit frontend application  
└── requirements.txt    \# Project dependencies

## **Setup and Installation**

Follow these steps to get the project up and running on your local machine.

### **1\. Prerequisites**

* Python 3.8 or higher

### **2\. Clone the Repository (Optional)**

If this project were in a Git repository, you would clone it. For now, just ensure your files are in a dedicated project folder.

### **3\. Create a Virtual Environment**

It is highly recommended to use a virtual environment to manage project dependencies.

\# For Windows  
python \-m venv venv  
.\\venv\\Scripts\\activate

\# For macOS/Linux  
python3 \-m venv venv  
source venv/bin/activate

### **4\. Install Dependencies**

Install all the required libraries from the requirements.txt file.

pip install \-r requirements.txt

## **Running the Application**

This project requires two separate processes to be running simultaneously in two different terminals: the backend API and the frontend web app.

### **Terminal 1: Start the Backend API**

In your first terminal, run the FastAPI server using uvicorn.

uvicorn app:app \--reload

The API will be available at http://127.0.0.1:8000. You can explore the interactive API documentation at http://127.0.0.1:8000/docs.

### **Terminal 2: Start the Frontend App**

In a new terminal, run the Streamlit application.

streamlit run frontend.py

A new tab should automatically open in your browser with the dashboard, typically at http://localhost:8501.

## **API Endpoints**

The backend exposes the following endpoints:

| Method | Endpoint | Description |
| :---- | :---- | :---- |
| GET | / | Root endpoint to check if the API is running. |
| GET | /stocks/{ticker}/info | Get general company information for a ticker. |
| GET | /stocks/{ticker}/history | Get historical OHLCV data for a ticker. |
| GET | /technicals/{ticker}/sma | Calculate the Simple Moving Average (SMA). |
| GET | /technicals/{ticker}/bbands | Calculate Bollinger Bands. |
| GET | /technicals/{ticker}/macd | Calculate Moving Average Convergence Divergence. |
| GET | /technicals/{ticker}/rsi | Calculate the Relative Strength Index. |

