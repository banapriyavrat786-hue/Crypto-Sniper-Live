import streamlit as st
import ccxt
import pandas as pd
import time

# --- AAPKI DELTA EXCHANGE API KEYS ---
API_KEY = "kQMGysaa9CZhlavh7FrAID7lsLamnd"
SECRET_KEY = "vU85g2uNhMuhbKeboyM8ho48snw3Kuix6yeML1mxlTTZaHrWh8BGjWh2pOou"

st.set_page_config(page_title="GRK Crypto Sniper V77", layout="wide")

@st.cache_resource
def get_exchange():
    return ccxt.delta({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'options': {'defaultType': 'future'}
    })

st.title("🏹 GRK CRYPTO SNIPER V77 | DELTA INDIA")

# --- SIDEBAR CONTROLS ---
symbol_ui = st.sidebar.selectbox("Pair", ["BTC/USDT", "ETH/USDT"])

with st.sidebar.expander("📐 Pivot Levels", expanded=True):
    prev_h = st.number_input("Prev High", value=65000.0)
    prev_l = st.number_input("Prev Low", value=63000.0)
    prev_c = st.number_input("Prev Close", value=64200.0)

try:
    ex = get_exchange()
    
    # --- ERROR FIX: CCXT FUTURES SYMBOL FORMAT ---
    # Futures market ke liye symbol ke aage ':USDT' lagana zaruri hota hai
    ccxt_symbol = f"{symbol_ui}:USDT"
    
    # Ticker aur Orderbook dono ek sath mangwate hain
    ticker = ex.fetch_ticker(ccxt_symbol)
    ob = ex.fetch_order_book(ccxt_symbol, limit=10)
    
    spot = ticker.get('last')
    
    # --- BULLETPROOF PRICE CHECK ---
    # Agar Ticker se price nahi mila, toh Orderbook ke current Bid/Ask se nikal lenge
    if spot is None:
        if ob['bids'] and ob['asks']:
            spot = (ob['bids'][0][0] + ob['asks'][0][0]) / 2

    if spot is None:
        raise ValueError(f"Symbol '{ccxt_symbol}' ka data abhi API par available nahi hai.")

    spot = float(spot)
    
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
    st.error(f"Market data syncing... Error Details: {e}")
    time.sleep(3)
    st.rerun()
