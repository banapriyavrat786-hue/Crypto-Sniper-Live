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

st.sidebar.divider()

# 🚨 NAYA: Safety & Risk Filters
st.sidebar.header("🔐 Safety Filters & Margin")
min_safety_score = st.sidebar.slider("Minimum Safety Score (%)", 0, 100, 75, 25)
sl_buffer_pct = st.sidebar.number_input("SL Safety Buffer (%)", min_value=0.0, value=0.10, step=0.05, help="Stoploss ko wicks se bachane ke liye extra gap")

st.sidebar.divider()
st.sidebar.header("🛡️ Trade Execution")
trade_qty = st.sidebar.number_input("Trade Quantity (Contracts)", min_value=1, value=20)
tp_pct = st.sidebar.number_input("Take Profit (%)", min_value=0.1, value=0.5, step=0.1)

try:
    ex = get_exchange()
    chart_ex = get_chart_exchange()
    
    # 1. LIVE DATA FETCHING
    ticker = ex.fetch_ticker(ccxt_symbol)
    ob = ex.fetch_order_book(ccxt_symbol, limit=20)
    info = ticker.get('info') or {}
    
    funding_rate = float(info.get('funding_rate') or 0.0)
    mark_basis = float(info.get('mark_basis') or 0.0) 
    vwap = float(info.get('vwap') or ticker.get('vwap') or 0.0) 
    contract_value = float(info.get('contract_value') or 1.0) 
    
    oi_raw = info.get('open_interest')
    oi = float(oi_raw) if oi_raw is not None else 0.0
    vol_raw = info.get('volume_24h')
    volume = float(vol_raw) if vol_raw is not None else float(ticker.get('baseVolume') or 0.0)
    
    # 2. SMA & VOLATILITY DATA FETCHING
    ohlcv = chart_ex.fetch_ohlcv(kucoin_symbol, timeframe, limit=sma_period + 5)
    if not ohlcv or len(ohlcv) < sma_period:
        current_sma = 0
        avg_volatility = 0.0
    else:
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        
        current_sma = float(df['close'].rolling(window=sma_period).mean().iloc[-1])
        
        # 🚨 NAYA: Market Condition & Volatility Calculation (Last 5 candles)
        df['range_pct'] = (df['high'] - df['low']) / df['close'] * 100
        avg_volatility = float(df['range_pct'].tail(5).mean())
        
    # 3. LIVE PRICE & ORDERBOOK
    if ob['bids'] and ob['asks']:
        best_bid = ob['bids'][0][0]  
        best_ask = ob['asks'][0][0]  
        spot = (best_bid + best_ask) / 2 
    else:
        spot = ticker.get('last', 0)
    spot = float(spot)

    trade_notional_usd = spot * contract_value * trade_qty

    bids_qty = sum([bid[1] for bid in ob['bids']])
    asks_qty = sum([ask[1] for ask in ob['asks']])
    total_qty = bids_qty + asks_qty
    buy_pressure = (bids_qty / total_qty) * 100 if total_qty > 0 else 50
    sell_pressure = (asks_qty / total_qty) * 100 if total_qty > 0 else 50

    # --- NAYA: MARKET CONDITION LOGIC ---
    market_condition = "Unknown"
    if avg_volatility > 0.8: # Adjust this threshold based on timeframe (0.8% in 1m/5m is highly volatile)
        market_condition = "High Volatility 🌪️ (Risky)"
    elif (spot > current_sma and spot > vwap) or (spot < current_sma and spot < vwap):
        market_condition = "Stable Trending 🌊 (Safe)"
    else:
        market_condition = "Choppy / Sideways 🚧 (Wait)"

    # --- NAYA: SAFETY SCORE CALCULATION (Out of 100%) ---
    long_score = 0
    short_score = 0
    
    if spot > current_sma: long_score += 25
    if spot < current_sma: short_score += 25
    
    if spot > vwap: long_score += 25
    if spot < vwap: short_score += 25
    
    if buy_pressure > 55: long_score += 25
    if sell_pressure > 55: short_score += 25
    
    if funding_rate < 0: long_score += 25
    if funding_rate > 0: short_score += 25

    # --- UI: QUANT DATA DASHBOARD ---
    st.subheader("🔬 Risk & Market Condition Desk")
    q1, q2, q3, q4 = st.columns(4)
    
    if "Risky" in market_condition:
        q1.metric("Market Condition", f"{avg_volatility:.2f}% Vol", market_condition, delta_color="inverse")
    elif "Safe" in market_condition:
        q1.metric("Market Condition", f"{avg_volatility:.2f}% Vol", market_condition, delta_color="normal")
    else:
        q1.metric("Market Condition", f"{avg_volatility:.2f}% Vol", market_condition, delta_color="off")
        
    q2.metric("Safety Score (LONG)", f"{long_score}%", "Max 100%")
    q3.metric("Safety Score (SHORT)", f"{short_score}%", "Max 100%")
    q4.metric("VWAP (True Trend)", f"${vwap:,.2f}", f"Diff: ${abs(spot-vwap):.1f}")

    st.divider()

    # --- ALGORITHMIC LOGIC ENGINE ---
    st.subheader("📋 Pro Logic Engine")
    chk1, chk2, chk3, chk4 = st.columns(4)
    
    if long_score >= 50: chk1.info("📈 1. Trend: Bullish Setup Detected")
    elif short_score >= 50: chk1.info("📉 1. Trend: Bearish Setup Detected")
    else: chk1.warning("⚖️ 1. Trend: Mixed Setup")

    if buy_pressure > 55: chk2.success(f"💪 2. Orderbook: Buyers ({buy_pressure:.0f}%)")
    elif sell_pressure > 55: chk2.error(f"🩸 2. Orderbook: Sellers ({sell_pressure:.0f}%)")
    else: chk2.warning("⚖️ 2. Orderbook: Neutral")

    if funding_rate < 0 and mark_basis < 0: chk3.success("🧠 3. Smart Money: Squeeze Ready")
    elif funding_rate > 0 and mark_basis > 0: chk3.error("🧠 3. Smart Money: Overheated")
    else: chk3.warning("🧠 3. Smart Money: Neutral")

    # 🚨 STRICT SIGNAL CALCULATION (Based on User Safety Score)
    signal = "WAIT ⏳ (Safety < Req)"
    
    if long_score >= min_safety_score and "Risky" not in market_condition:
        signal = f"🟢 SAFE BUY ({long_score}% Match)"
    elif short_score >= min_safety_score and "Risky" not in market_condition:
        signal = f"🔴 SAFE SELL ({short_score}% Match)"
    elif "Risky" in market_condition:
        signal = "⚠️ WAIT ⏳ (Market Too Volatile)"
    
    chk4.metric("🎯 Final Safe Signal", signal)

    st.divider()

    # --- DYNAMIC TARGETS & RISK MANAGER ---
    current_time = datetime.now().strftime("%I:%M:%S %p")
    st.caption(f"⚡ Execution & Risk Desk | Last Updated: {current_time}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Execution Price", f"${spot:,.2f}")
    c2.metric(f"Trade Size ({trade_qty} Qty)", f"${trade_notional_usd:,.2f} USD")
    
    # 🚨 NAYA: Safety Buffer added to VWAP Stoploss
    if "BUY" in signal:
        tp = spot + (spot * (tp_pct/100))
        sl_base = vwap if vwap < spot else spot * 0.99
        sl = sl_base * (1 - sl_buffer_pct/100) # Added Safety Buffer
        c3.metric(f"🎯 Target (+{tp_pct}%)", f"${tp:,.2f}")
        c4.metric(f"🛡️ Safe Stoploss (VWAP - Buffer)", f"${sl:,.2f}")
    elif "SELL" in signal:
        tp = spot - (spot * (tp_pct/100))
        sl_base = vwap if vwap > spot else spot * 1.01
        sl = sl_base * (1 + sl_buffer_pct/100) # Added Safety Buffer
        c3.metric(f"🎯 Target (+{tp_pct}%)", f"${tp:,.2f}")
        c4.metric(f"🛡️ Safe Stoploss (VWAP + Buffer)", f"${sl:,.2f}")
    else:
        c3.metric("🎯 Target (TP)", "Awaiting Safe Signal...")
        c4.metric("🛡️ Stoploss (SL)", "Awaiting Safe Signal...")

    st.divider()

    # --- TRADE EXECUTION ---
    t1, t2 = st.columns(2)
    buy_clicked = t1.button("🟢 MARKET BUY LONG", use_container_width=True)
    sell_clicked = t2.button("🔴 MARKET SELL SHORT", use_container_width=True)

    if buy_clicked:
        try:
            ex.create_market_buy_order(ccxt_symbol, trade_qty)
            st.success(f"✅ Executed BUY! Size: ${trade_notional_usd:,.2f}")
        except Exception as e:
            st.error(f"❌ Execution Error: {e}")
            
    if sell_clicked:
        try:
            ex.create_market_sell_order(ccxt_symbol, trade_qty)
            st.success(f"✅ Executed SELL! Size: ${trade_notional_usd:,.2f}")
        except Exception as e:
            st.error(f"❌ Execution Error: {e}")

    # Auto-Reload Loop
    time.sleep(3)
    st.rerun()

except Exception as e:
    st.error(f"Re-syncing data pipeline... Error Details: {e}")
    time.sleep(4)
    st.rerun()
