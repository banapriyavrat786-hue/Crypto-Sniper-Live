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

# --- SIDEBAR: SETTINGS & RISK MANAGEMENT ---
st.sidebar.header("⚙️ Strategy Settings")
symbol_ui = st.sidebar.selectbox("Pair", ["BTC/USDT", "ETH/USDT"])

with st.sidebar.expander("📐 Pivot Levels", expanded=True):
    prev_h = st.number_input("Prev High", value=65000.0)
    prev_l = st.number_input("Prev Low", value=63000.0)
    prev_c = st.number_input("Prev Close", value=64200.0)

st.sidebar.divider()

st.sidebar.header("🛡️ Risk Management (SL & Target)")
trade_qty = st.sidebar.number_input("Quantity", min_value=1, value=1)
sl_pct = st.sidebar.number_input("Stop Loss (%)", min_value=0.1, value=1.0, step=0.1)
tp_pct = st.sidebar.number_input("Target (%)", min_value=0.1, value=2.0, step=0.1)

try:
    ex = get_exchange()
    ccxt_symbol = f"{symbol_ui}:USDT"
    
    # --- DATA FETCHING ---
    ticker = ex.fetch_ticker(ccxt_symbol)
    ob = ex.fetch_order_book(ccxt_symbol, limit=20)
    
    spot = ticker.get('last')
    if spot is None:
        if ob['bids'] and ob['asks']:
            spot = (ob['bids'][0][0] + ob['asks'][0][0]) / 2
    if spot is None:
        raise ValueError("Data nahi mil raha hai.")
    
    spot = float(spot)
    pivot = (prev_h + prev_l + prev_c) / 3

    # --- BUYER/SELLER PRESSURE ---
    bids_qty = sum([bid[1] for bid in ob['bids']])
    asks_qty = sum([ask[1] for ask in ob['asks']])
    total_qty = bids_qty + asks_qty
    
    buy_pressure = (bids_qty / total_qty) * 100 if total_qty > 0 else 50
    sell_pressure = (asks_qty / total_qty) * 100 if total_qty > 0 else 50

    # --- STRATEGY CHECKLIST & LOGIC ---
    is_price_above_pivot = spot > pivot
    is_buyer_strong = buy_pressure > 55.0
    is_seller_strong = sell_pressure > 55.0

    st.subheader("📋 Algorithmic Entry Checklist")
    chk1, chk2, chk3 = st.columns(3)
    
    # Checklist Display
    chk1.info(f"📈 Trend Check: {'Bullish (Price > Pivot)' if is_price_above_pivot else 'Bearish (Price < Pivot)'}")
    if is_buyer_strong:
        chk2.success(f"💪 Volume Check: Buyers Strong ({buy_pressure:.1f}%)")
    elif is_seller_strong:
        chk2.error(f"🩸 Volume Check: Sellers Strong ({sell_pressure:.1f}%)")
    else:
        chk2.warning("⚖️ Volume Check: Neutral Market")

    # Signal Generation
    signal = "WAIT ⏳"
    if is_price_above_pivot and is_buyer_strong:
        signal = "🟢 BUY LONG SIGNAL"
    elif not is_price_above_pivot and is_seller_strong:
        signal = "🔴 SELL SHORT SIGNAL"
    
    chk3.metric("Sniper Status", signal)

    st.divider()

    # --- DASHBOARD METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Price", f"${spot:,.2f}")
    c2.metric("Pivot (P)", f"${pivot:,.2f}")
    
    # Target and SL Calculation based on signal
    if "BUY" in signal:
        target_price = spot + (spot * (tp_pct/100))
        sl_price = spot - (spot * (sl_pct/100))
        c3.metric("🎯 Target (TP)", f"${target_price:,.2f}", f"+{tp_pct}%")
        c4.metric("🛡️ Stoploss (SL)", f"${sl_price:,.2f}", f"-{sl_pct}%")
    elif "SELL" in signal:
        target_price = spot - (spot * (tp_pct/100))
        sl_price = spot + (spot * (sl_pct/100))
        c3.metric("🎯 Target (TP)", f"${target_price:,.2f}", f"+{tp_pct}%")
        c4.metric("🛡️ Stoploss (SL)", f"${sl_price:,.2f}", f"-{sl_pct}%")
    else:
        c3.metric("🎯 Target (TP)", "Waiting for Signal...")
        c4.metric("🛡️ Stoploss (SL)", "Waiting for Signal...")

    st.divider()

    # --- LIVE TRADE PANEL (Manual Execution) ---
    t1, t2 = st.columns(2)
    buy_clicked = t1.button("🟢 EXECUTE BUY LONG", use_container_width=True)
    sell_clicked = t2.button("🔴 EXECUTE SELL SHORT", use_container_width=True)

    if buy_clicked:
        try:
            order = ex.create_market_buy_order(ccxt_symbol, trade_qty)
            st.success("✅ Buy Order Placed!")
            # Note: API call for setting SL/TP automatically requires advanced ccxt params
        except Exception as e:
            st.error(f"❌ Trade Error: {e}")
            
    if sell_clicked:
        try:
            order = ex.create_market_sell_order(ccxt_symbol, trade_qty)
            st.success("✅ Sell Order Placed!")
        except Exception as e:
            st.error(f"❌ Trade Error: {e}")

    # Refresh Loop
    time.sleep(2)
    st.rerun()

except Exception as e:
    st.error(f"Market data syncing... Error Details: {e}")
    time.sleep(3)
    st.rerun()
