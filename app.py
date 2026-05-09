import streamlit as st
import ccxt
import pandas as pd
import time

# --- AAPKI DELTA EXCHANGE API KEYS ---
API_KEY = "FI831QLhYTsF8M6MhoCKFgHfy0Tf12"
SECRET_KEY = "x6LK5Q75IKpfOMjnrIR9ee85EwRhresB7Jp1SY333XplXum8FSpp2iVAalfA"

st.set_page_config(page_title="GRK Crypto Sniper V77", layout="wide")

@st.cache_resource
def get_exchange():
    return ccxt.delta({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'options': {'defaultType': 'future'}
    })

st.title("🏹 GRK CRYPTO SNIPER V77 | DELTA INDIA")

# --- SIDEBAR: SETTINGS & TRADING ---
st.sidebar.header("⚙️ Settings")
symbol_ui = st.sidebar.selectbox("Pair", ["BTC/USDT", "ETH/USDT"])

with st.sidebar.expander("📐 Pivot Levels", expanded=True):
    prev_h = st.number_input("Prev High", value=65000.0)
    prev_l = st.number_input("Prev Low", value=63000.0)
    prev_c = st.number_input("Prev Close", value=64200.0)

st.sidebar.divider()

# --- LIVE TRADE PANEL ---
st.sidebar.header("⚡ Live Trading Panel")
trade_qty = st.sidebar.number_input("Quantity (Contracts)", min_value=1, value=1)

t1, t2 = st.sidebar.columns(2)
buy_clicked = t1.button("🟢 BUY LONG")
sell_clicked = t2.button("🔴 SELL SHORT")

try:
    ex = get_exchange()
    ccxt_symbol = f"{symbol_ui}:USDT"
    
    # --- ORDER EXECUTION LOGIC ---
    if buy_clicked:
        try:
            order = ex.create_market_buy_order(ccxt_symbol, trade_qty)
            st.sidebar.success("✅ Buy Order Placed Successfully!")
        except Exception as e:
            st.sidebar.error(f"❌ Trade Error: {e}")
            
    if sell_clicked:
        try:
            order = ex.create_market_sell_order(ccxt_symbol, trade_qty)
            st.sidebar.success("✅ Sell Order Placed Successfully!")
        except Exception as e:
            st.sidebar.error(f"❌ Trade Error: {e}")

    # --- DATA FETCHING ---
    ticker = ex.fetch_ticker(ccxt_symbol)
    ob = ex.fetch_order_book(ccxt_symbol, limit=20) # Limit badhayi Safety Check ke liye
    
    spot = ticker.get('last')
    if spot is None:
        if ob['bids'] and ob['asks']:
            spot = (ob['bids'][0][0] + ob['asks'][0][0]) / 2

    if spot is None:
        raise ValueError("Data nahi mil raha hai.")
    spot = float(spot)
    pivot = (prev_h + prev_l + prev_c) / 3

    # --- BUYER/SELLER SAFETY PERCENTAGE ---
    bids_qty = sum([bid[1] for bid in ob['bids']])
    asks_qty = sum([ask[1] for ask in ob['asks']])
    total_qty = bids_qty + asks_qty
    
    buy_pressure = (bids_qty / total_qty) * 100 if total_qty > 0 else 50
    sell_pressure = (asks_qty / total_qty) * 100 if total_qty > 0 else 50

    # --- DASHBOARD METRICS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Live Price", f"${spot:,.2f}")
    c2.metric("Pivot (P)", f"${pivot:,.2f}", delta=f"{round(spot-pivot, 2)}")
    
    # Safety Percentage UI
    c3.metric("🟢 Buyer Safety (Pressure)", f"{buy_pressure:.1f}%", f"{buy_pressure - 50:.1f}%")
    st.progress(int(buy_pressure) / 100)
    st.caption(f"Market Power: 🟢 Buyers {buy_pressure:.1f}% | 🔴 Sellers {sell_pressure:.1f}%")

    st.divider()

    # --- ORDERBOOK ---
    st.subheader("⚔️ Live Orderbook Battle")
    col1, col2 = st.columns(2)
    with col1:
        st.write("🟢 Bids (Buyers)")
        st.dataframe(pd.DataFrame(ob['bids'], columns=['Price', 'Qty']).head(5), use_container_width=True)
    with col2:
        st.write("🔴 Asks (Sellers)")
        st.dataframe(pd.DataFrame(ob['asks'], columns=['Price', 'Qty']).head(5), use_container_width=True)

    # Refresh Loop
    time.sleep(2)
    st.rerun()

except Exception as e:
    st.error(f"Market data syncing... Error Details: {e}")
    time.sleep(3)
    st.rerun()
