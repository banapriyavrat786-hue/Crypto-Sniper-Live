import streamlit as st
import ccxt
import pandas as pd
import time

# --- AAPKI DELTA EXCHANGE API KEYS ---
API_KEY = "kQMGysaa9CZhlavh7FrAID7lsLamnd"
SECRET_KEY = "vU85g2uNhMuhbKeboyM8ho48snw3Kuix6yeML1mxlTTZaHrWh8BGjWh2pOou"

st.set_page_config(page_title="GRK Crypto Sniper V77", layout="wide")

# --- EXCHANGE CONNECTION FIX ---
@st.cache_resource
def get_exchange():
    return ccxt.delta({  # Yahan mistake thi jise theek kar diya gaya hai
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'options': {'defaultType': 'future'}
    })

st.title("🏹 GRK CRYPTO SNIPER V77 | DELTA INDIA")

# --- SIDEBAR CONTROLS ---
# Delta me standard pair ka naam aise hi hota hai
symbol = st.sidebar.selectbox("Pair", ["BTC/USDT", "ETH/USDT"])

with st.sidebar.expander("📐 Pivot Levels", expanded=True):
    prev_h = st.number_input("Prev High", value=65000.0)
    prev_l = st.number_input("Prev Low", value=63000.0)
    prev_c = st.number_input("Prev Close", value=64200.0)

try:
    ex = get_exchange()
    
    # Live Price Fetching
    ticker = ex.fetch_ticker(symbol)
    spot = ticker['last']
    
    # Pivot Calculation Logic
    pivot = (prev_h + prev_l + prev_c) / 3
    s1 = (2 * pivot) - prev_h
    r1 = (2 * pivot) - prev_l

    # Dashboard Metrics
    c1, c2 = st.columns(2)
    c1.metric("Live Price", f"${spot:,.2f}")
    c2.metric("Pivot (P)", f"${pivot:,.2f}", delta=f"{round(spot-pivot, 2)}")

    st.divider()
    
    # Live Orderbook
    ob = ex.fetch_order_book(symbol, limit=10)
    st.subheader("⚔️ Live Orderbook Battle")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("🟢 Bids (Buyers)")
        st.dataframe(pd.DataFrame(ob['bids'], columns=['Price', 'Qty']).head(5), use_container_width=True)
    with col2:
        st.write("🔴 Asks (Sellers)")
        st.dataframe(pd.DataFrame(ob['asks'], columns=['Price', 'Qty']).head(5), use_container_width=True)

    # Sniper Auto-Refresh Speed
    time.sleep(2)
    st.rerun()

except Exception as e:
    # Agar data aane me thoda time lage ya API issue ho
    st.error(f"🔄 Market data syncing... Error Details: {e}")
    time.sleep(3)
    st.rerun()
