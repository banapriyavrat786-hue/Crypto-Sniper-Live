import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- 🚨 YAHAN APNI KEYS KHUD PASTE KAREIN 🚨 ---
API_KEY = "YAHAN_APNI_API_KEY_PASTE_KAREIN"
SECRET_KEY = "YAHAN_APNI_SECRET_KEY_PASTE_KAREIN"

st.set_page_config(page_title="GRK Quant Sniper V77", layout="wide")

@st.cache_resource
def get_exchange():
    return ccxt.delta({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'options': {'defaultType': 'future'}
    })

@st.cache_resource
def get_chart_exchange():
    return ccxt.kucoin()

st.title("🏹 GRK PRO QUANT SNIPER V77 | DELTA INDIA")

# --- SIDEBAR: SETTINGS ---
st.sidebar.header("⚙️ Market Selection")
ccxt_symbol = st.sidebar.text_input("Contract Symbol", value="BTC/USDT:USDT")

base_coin = ccxt_symbol.split('/')[0] if '/' in ccxt_symbol else 'BTC'
kucoin_symbol = f"{base_coin}-USDT"

timeframe = st.sidebar.selectbox("Timeframe (SMA)", ["1m", "5m", "15m", "1h", "4h", "1d"], index=1)
sma_period = st.sidebar.number_input("SMA Period", min_value=5, value=20, step=1)
trade_qty = st.sidebar.number_input("Trade Quantity", min_value=1, value=1)

try:
    ex = get_exchange()
    chart_ex = get_chart_exchange()
    
    # 1. LIVE DATA FETCHING
    ticker = ex.fetch_ticker(ccxt_symbol)
    ob = ex.fetch_order_book(ccxt_symbol, limit=20)
    info = ticker.get('info') or {}
    
    # --- 🧠 EXTRACTING ALL HIDDEN PRO DATA ---
    
    # Fundamental & Sentiment
    funding_rate = float(info.get('funding_rate') or 0.0)
    mark_basis = float(info.get('mark_basis') or 0.0) # Premium/Discount indicator
    vwap = float(info.get('vwap') or ticker.get('vwap') or 0.0) # True average price
    
    # Exchange Limits (Dynamic Targets/SL)
    price_band = info.get('price_band') or {}
    upper_limit = float(price_band.get('upper_limit') or 0.0)
    lower_limit = float(price_band.get('lower_limit') or 0.0)
    
    # Volume & OI
    oi_raw = info.get('open_interest')
    oi = float(oi_raw) if oi_raw is not None else 0.0
    vol_raw = info.get('volume_24h')
    volume = float(vol_raw) if vol_raw is not None else float(ticker.get('baseVolume') or 0.0)
    
    # Greeks
    greeks_data = info.get('greeks') or {}
    delta_val = float(greeks_data.get('delta') or 0.0)
    theta_val = float(greeks_data.get('theta') or 0.0)
    gamma_val = float(greeks_data.get('gamma') or 0.0)
    iv_raw = greeks_data.get('iv') or info.get('implied_volatility')
    iv_val = float(iv_raw) if iv_raw is not None else 0.0
    
    # 2. SMA DATA FETCHING
    ohlcv = chart_ex.fetch_ohlcv(kucoin_symbol, timeframe, limit=sma_period + 5)
    if not ohlcv or len(ohlcv) < sma_period:
        current_sma = 0
    else:
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        current_sma = float(df['close'].astype(float).rolling(window=sma_period).mean().iloc[-1])
        
    # 3. LIVE PRICE & ORDERBOOK
    if ob['bids'] and ob['asks']:
        best_bid = ob['bids'][0][0]  
        best_ask = ob['asks'][0][0]  
        spot = (best_bid + best_ask) / 2 
    else:
        spot = ticker.get('last', 0)
    spot = float(spot)

    bids_qty = sum([bid[1] for bid in ob['bids']])
    asks_qty = sum([ask[1] for ask in ob['asks']])
    total_qty = bids_qty + asks_qty
    buy_pressure = (bids_qty / total_qty) * 100 if total_qty > 0 else 50
    sell_pressure = (asks_qty / total_qty) * 100 if total_qty > 0 else 50

    # --- UI: QUANT DATA DASHBOARD ---
    st.subheader("🔬 Quant & Smart Money Data")
    q1, q2, q3, q4, q5 = st.columns(5)
    
    # VWAP Check
    if spot > vwap:
        q1.metric("VWAP (True Trend)", f"${vwap:,.2f}", "Bullish Control 🟢")
    else:
        q1.metric("VWAP (True Trend)", f"${vwap:,.2f}", "-Bearish Control 🔴")
        
    # Basis Check
    if mark_basis > 0:
        q2.metric("Premium/Basis", f"{mark_basis:,.4f}", "Market Overheated 🔥")
    else:
        q2.metric("Discount/Basis", f"{mark_basis:,.4f}", "-Market Oversold ❄️")
        
    # Funding Rate
    if funding_rate < 0:
        q3.metric("Funding Rate", f"{funding_rate:,.6f}", "Short Squeeze Chance 🚀")
    else:
        q3.metric("Funding Rate", f"{funding_rate:,.6f}", "-Long Squeeze Chance 🩸")
        
    q4.metric("Exchange Upper Limit", f"${upper_limit:,.2f}")
    q5.metric("Exchange Lower Limit", f"${lower_limit:,.2f}")

    st.divider()

    # --- UI: STANDARD MARKET DATA ---
    st.subheader("📊 Market Data & Options Greeks")
    g1, g2, g3, g4, g5, g6 = st.columns(6)
    g1.metric("Volume (Base)", f"{volume:,.2f}")
    g2.metric("Open Interest (OI)", f"{oi:,.2f}")
    g3.metric("Delta (Δ)", f"{delta_val:,.4f}")
    g4.metric("Theta (Θ)", f"{theta_val:,.4f}")
    g5.metric("Gamma (Γ)", f"{gamma_val:,.6f}")
    g6.metric("Implied Volatility (IV)", f"{iv_val:,.2f}%")

    st.divider()

    # --- ALGORITHMIC LOGIC ENGINE ---
    st.subheader("📋 Pro Logic Engine")
    chk1, chk2, chk3, chk4 = st.columns(4)
    
    # 1. Trend (VWAP is stronger than SMA for day trading)
    is_trend_up = spot > vwap and spot > current_sma
    is_trend_down = spot < vwap and spot < current_sma
    
    if is_trend_up: chk1.info("📈 1. Trend: Strong Bullish (>VWAP & SMA)")
    elif is_trend_down: chk1.info("📉 1. Trend: Strong Bearish (<VWAP & SMA)")
    else: chk1.warning("⚖️ 1. Trend: Mixed/Sideways")

    # 2. Pressure
    if buy_pressure > 55: chk2.success(f"💪 2. Orderbook: Buyers ({buy_pressure:.0f}%)")
    elif sell_pressure > 55: chk2.error(f"🩸 2. Orderbook: Sellers ({sell_pressure:.0f}%)")
    else: chk2.warning("⚖️ 2. Orderbook: Neutral")

    # 3. Smart Money (Funding + Basis)
    if funding_rate < 0 and mark_basis < 0:
        chk3.success("🧠 3. Smart Money: Perfect Squeeze Setup")
    elif funding_rate > 0 and mark_basis > 0:
        chk3.error("🧠 3. Smart Money: Overheated (Correction Due)")
    else:
        chk3.warning("🧠 3. Smart Money: Neutral Setup")

    # 🚨 FINAL SIGNAL CALCULATION
    signal = "WAIT ⏳"
    # Buy Condition: Trend UP + Orderbook BUY + Funding Negative (Shorts Trapped)
    if is_trend_up and buy_pressure > 55 and funding_rate <= 0:
        signal = "🟢 SNIPER BUY (High Conviction)"
    # Sell Condition: Trend DOWN + Orderbook SELL + Funding Positive (Longs Trapped)
    elif is_trend_down and sell_pressure > 55 and funding_rate >= 0:
        signal = "🔴 SNIPER SELL (High Conviction)"
    
    chk4.metric("🎯 Bot Final Signal", signal)

    st.divider()

    # --- DYNAMIC TARGETS (Based on Exchange Limits & VWAP) ---
    current_time = datetime.now().strftime("%I:%M:%S %p")
    st.caption(f"⚡ Dynamic Execution Panel | Last Updated: {current_time}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Execution Price", f"${spot:,.2f}")
    c2.metric("SMA Indicator", f"${current_sma:,.2f}")
    
    # Smart Target Logic
    if "BUY" in signal:
        tp = spot + ((upper_limit - spot) * 0.2) # Target is 20% of the way to the daily upper limit
        sl = vwap if vwap < spot else spot * 0.99 # SL is VWAP (Dynamic support)
        c3.metric("🎯 Dynamic Target (TP)", f"${tp:,.2f}", "Calculated from Upper Limit")
        c4.metric("🛡️ Dynamic Stoploss (SL)", f"${sl:,.2f}", "Calculated from VWAP")
    elif "SELL" in signal:
        tp = spot - ((spot - lower_limit) * 0.2) 
        sl = vwap if vwap > spot else spot * 1.01
        c3.metric("🎯 Dynamic Target (TP)", f"${tp:,.2f}", "Calculated from Lower Limit")
        c4.metric("🛡️ Dynamic Stoploss (SL)", f"${sl:,.2f}", "Calculated from VWAP")
    else:
        c3.metric("🎯 Target (TP)", "Awaiting Signal...")
        c4.metric("🛡️ Stoploss (SL)", "Awaiting Signal...")

    st.divider()

    # --- TRADE EXECUTION ---
    t1, t2 = st.columns(2)
    buy_clicked = t1.button("🟢 MARKET BUY LONG", use_container_width=True)
    sell_clicked = t2.button("🔴 MARKET SELL SHORT", use_container_width=True)

    if buy_clicked:
        try:
            ex.create_market_buy_order(ccxt_symbol, trade_qty)
            st.success(f"✅ Executed BUY for {trade_qty} {ccxt_symbol}")
        except Exception as e:
            st.error(f"❌ Execution Error: {e}")
            
    if sell_clicked:
        try:
            ex.create_market_sell_order(ccxt_symbol, trade_qty)
            st.success(f"✅ Executed SELL for {trade_qty} {ccxt_symbol}")
        except Exception as e:
            st.error(f"❌ Execution Error: {e}")

    # Auto-Reload Loop
    time.sleep(3)
    st.rerun()

except Exception as e:
    st.error(f"Re-syncing data pipeline... Error Details: {e}")
    time.sleep(4)
    st.rerun()
