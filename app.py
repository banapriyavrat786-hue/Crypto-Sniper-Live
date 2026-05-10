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
st.sidebar.header("🛡️ Trade Execution Settings")
trade_qty = st.sidebar.number_input("Trade Quantity (Contracts)", min_value=1, value=20)
# Wapas aapka apna TP/SL Percentage le aaye taaki scalping sahi ho!
tp_pct = st.sidebar.number_input("Take Profit (%)", min_value=0.1, value=0.5, step=0.1)
sl_pct = st.sidebar.number_input("Stop Loss (%)", min_value=0.1, value=0.3, step=0.1)

try:
    ex = get_exchange()
    chart_ex = get_chart_exchange()
    
    # 1. LIVE DATA FETCHING
    ticker = ex.fetch_ticker(ccxt_symbol)
    ob = ex.fetch_order_book(ccxt_symbol, limit=20)
    info = ticker.get('info') or {}
    
    # --- 🧠 EXTRACTING ALL HIDDEN PRO DATA ---
    funding_rate = float(info.get('funding_rate') or 0.0)
    mark_basis = float(info.get('mark_basis') or 0.0) 
    vwap = float(info.get('vwap') or ticker.get('vwap') or 0.0) 
    
    # 🚨 THE MISSING PIECE: Contract Value & Sizing
    # Default 1.0 manenge, par Delta BTC ke liye 0.001 bhejta hai
    contract_value = float(info.get('contract_value') or 1.0) 
    
    oi_raw = info.get('open_interest')
    oi = float(oi_raw) if oi_raw is not None else 0.0
    vol_raw = info.get('volume_24h')
    volume = float(vol_raw) if vol_raw is not None else float(ticker.get('baseVolume') or 0.0)
    
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

    # 🚨 RISK DESK CALCULATIONS (Asli USD Size)
    trade_notional_usd = spot * contract_value * trade_qty

    bids_qty = sum([bid[1] for bid in ob['bids']])
    asks_qty = sum([ask[1] for ask in ob['asks']])
    total_qty = bids_qty + asks_qty
    buy_pressure = (bids_qty / total_qty) * 100 if total_qty > 0 else 50
    sell_pressure = (asks_qty / total_qty) * 100 if total_qty > 0 else 50

    # --- UI: QUANT DATA DASHBOARD ---
    st.subheader("🔬 Quant & Smart Money Data")
    q1, q2, q3, q4 = st.columns(4)
    
    if spot > vwap:
        q1.metric("VWAP (True Trend)", f"${vwap:,.2f}", "Bullish Control 🟢")
    else:
        q1.metric("VWAP (True Trend)", f"${vwap:,.2f}", "-Bearish Control 🔴")
        
    if mark_basis > 0:
        q2.metric("Premium/Basis", f"{mark_basis:,.4f}", "Market Overheated 🔥")
    else:
        q2.metric("Discount/Basis", f"{mark_basis:,.4f}", "-Market Oversold ❄️")
        
    if funding_rate < 0:
        q3.metric("Funding Rate", f"{funding_rate:,.6f}", "Short Squeeze Chance 🚀")
    else:
        q3.metric("Funding Rate", f"{funding_rate:,.6f}", "-Long Squeeze Chance 🩸")
        
    q4.metric("Contract Multiplier", f"{contract_value} {base_coin}", "1 Qty Value")

    st.divider()

    # --- ALGORITHMIC LOGIC ENGINE ---
    st.subheader("📋 Pro Logic Engine")
    chk1, chk2, chk3, chk4 = st.columns(4)
    
    is_trend_up = spot > vwap and spot > current_sma
    is_trend_down = spot < vwap and spot < current_sma
    
    if is_trend_up: chk1.info("📈 1. Trend: Strong Bullish (>VWAP & SMA)")
    elif is_trend_down: chk1.info("📉 1. Trend: Strong Bearish (<VWAP & SMA)")
    else: chk1.warning("⚖️ 1. Trend: Mixed/Sideways")

    if buy_pressure > 55: chk2.success(f"💪 2. Orderbook: Buyers ({buy_pressure:.0f}%)")
    elif sell_pressure > 55: chk2.error(f"🩸 2. Orderbook: Sellers ({sell_pressure:.0f}%)")
    else: chk2.warning("⚖️ 2. Orderbook: Neutral")

    if funding_rate < 0 and mark_basis < 0:
        chk3.success("🧠 3. Smart Money: Perfect Squeeze Setup")
    elif funding_rate > 0 and mark_basis > 0:
        chk3.error("🧠 3. Smart Money: Overheated (Correction Due)")
    else:
        chk3.warning("🧠 3. Smart Money: Neutral Setup")

    signal = "WAIT ⏳"
    if is_trend_up and buy_pressure > 55 and funding_rate <= 0:
        signal = "🟢 SNIPER BUY (High Conviction)"
    elif is_trend_up and buy_pressure > 55:
        signal = "🟢 BUY LONG"
    elif is_trend_down and sell_pressure > 55 and funding_rate >= 0:
        signal = "🔴 SNIPER SELL (High Conviction)"
    elif is_trend_down and sell_pressure > 55:
        signal = "🔴 SELL SHORT"
    
    chk4.metric("🎯 Bot Final Signal", signal)

    st.divider()

    # --- DYNAMIC TARGETS & RISK MANAGER ---
    current_time = datetime.now().strftime("%I:%M:%S %p")
    st.caption(f"⚡ Execution & Risk Desk | Last Updated: {current_time}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Execution Price", f"${spot:,.2f}")
    
    # Ye apko batayega ki actually aap kitne dollar ka trade le rahe ho
    c2.metric(f"Trade Size ({trade_qty} Qty)", f"${trade_notional_usd:,.2f} USD")
    
    # Scalping Targets based on User %
    if "BUY" in signal:
        tp = spot + (spot * (tp_pct/100))
        sl = spot - (spot * (sl_pct/100))
        c3.metric(f"🎯 Target (+{tp_pct}%)", f"${tp:,.2f}")
        c4.metric(f"🛡️ Stoploss (-{sl_pct}%)", f"${sl:,.2f}")
    elif "SELL" in signal:
        tp = spot - (spot * (tp_pct/100))
        sl = spot + (spot * (sl_pct/100))
        c3.metric(f"🎯 Target (+{tp_pct}%)", f"${tp:,.2f}")
        c4.metric(f"🛡️ Stoploss (-{sl_pct}%)", f"${sl:,.2f}")
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
