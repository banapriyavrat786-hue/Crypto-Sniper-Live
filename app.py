import streamlit as st
import ccxt
import pandas as pd
import time
from datetime import datetime

# --- 🚨 YAHAN APNI KEYS KHUD PASTE KAREIN 🚨 ---
API_KEY = "YAHAN_APNI_API_KEY_PASTE_KAREIN"
SECRET_KEY = "YAHAN_APNI_SECRET_KEY_PASTE_KAREIN"

st.set_page_config(page_title="GRK F&O Sniper V77", layout="wide")

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

st.title("🏹 GRK ULTIMATE F&O SNIPER | DELTA INDIA")

# --- SIDEBAR: SETTINGS & RISK MANAGEMENT ---
st.sidebar.header("⚙️ Strategy Settings")

st.sidebar.caption("Futures Ex: BTC/USDT:USDT")
st.sidebar.caption("Options Ex: BTC/USDT:USDT-240531-70000-C")
ccxt_symbol = st.sidebar.text_input("Exact Contract Symbol", value="BTC/USDT:USDT")

base_coin = ccxt_symbol.split('/')[0] if '/' in ccxt_symbol else 'BTC'
kucoin_symbol = f"{base_coin}-USDT"

timeframe = st.sidebar.selectbox("Timeframe (SMA)", ["1m", "5m", "15m", "1h", "4h", "1d"], index=1)
sma_period = st.sidebar.number_input("SMA Period", min_value=5, value=20, step=1)

st.sidebar.divider()

st.sidebar.header("🛡️ Risk Management (SL & Target)")
trade_qty = st.sidebar.number_input("Quantity", min_value=1, value=1)
sl_pct = st.sidebar.number_input("Stop Loss (%)", min_value=0.1, value=1.0, step=0.1)
tp_pct = st.sidebar.number_input("Target (%)", min_value=0.1, value=2.0, step=0.1)

try:
    ex = get_exchange()
    chart_ex = get_chart_exchange()
    
    # 1. LIVE DATA FETCHING
    ticker = ex.fetch_ticker(ccxt_symbol)
    ob = ex.fetch_order_book(ccxt_symbol, limit=20)
    
    # 🚨 THE EXACT FIX (Based on your Delta API Docs Video)
    # Agar info 'None' aata hai, toh usko empty dict {} maan lenge taaki crash na ho
    info = ticker.get('info') or {}
    
    # Volume aur OI nikalne ka exact tarika
    oi_raw = info.get('open_interest')
    oi = float(oi_raw) if oi_raw is not None else 0.0
    
    vol_raw = info.get('volume_24h')
    volume = float(vol_raw) if vol_raw is not None else float(ticker.get('baseVolume') or 0.0)
    
    # Greeks nikalne ka 100% crash-proof tarika (Agar greeks 'null' hain toh {} use hoga)
    greeks_data = info.get('greeks') or {}
    
    delta_val = float(greeks_data.get('delta') or 0.0)
    theta_val = float(greeks_data.get('theta') or 0.0)
    gamma_val = float(greeks_data.get('gamma') or 0.0)
    
    # IV ke liye fallback logic
    iv_raw = greeks_data.get('iv') or info.get('implied_volatility')
    iv_val = float(iv_raw) if iv_raw is not None else 0.0
    
    # 2. SMA DATA FETCHING (KuCoin Spot Data)
    ohlcv = chart_ex.fetch_ohlcv(kucoin_symbol, timeframe, limit=sma_period + 5)
        
    if not ohlcv or len(ohlcv) < sma_period:
        current_sma = 0
        is_price_above_sma = False
    else:
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['close'] = df['close'].astype(float)
        df['SMA'] = df['close'].rolling(window=sma_period).mean()
        current_sma = df['SMA'].dropna().iloc[-1]
        
    # 3. 100% LIVE PRICE LOGIC (Seedha Orderbook se)
    if ob['bids'] and ob['asks']:
        best_bid = ob['bids'][0][0]  
        best_ask = ob['asks'][0][0]  
        spot = (best_bid + best_ask) / 2 
    else:
        spot = ticker.get('last', 0)
    
    spot = float(spot)
    is_price_above_sma = spot > current_sma if current_sma > 0 else False

    # 4. BUYER/SELLER PRESSURE
    bids_qty = sum([bid[1] for bid in ob['bids']])
    asks_qty = sum([ask[1] for ask in ob['asks']])
    total_qty = bids_qty + asks_qty
    
    buy_pressure = (bids_qty / total_qty) * 100 if total_qty > 0 else 50
    sell_pressure = (asks_qty / total_qty) * 100 if total_qty > 0 else 50

    is_buyer_strong = buy_pressure > 55.0
    is_seller_strong = sell_pressure > 55.0

    # --- UI DISPLAY: GREEKS & MARKET DATA ---
    st.subheader("📊 Market Data & Options Greeks")
    g1, g2, g3, g4, g5, g6 = st.columns(6)
    g1.metric("Volume (Base)", f"{volume:,.2f}")
    g2.metric("Open Interest (OI)", f"{oi:,.2f}")
    g3.metric("Delta (Δ)", f"{delta_val:,.4f}")
    g4.metric("Theta (Θ)", f"{theta_val:,.4f}")
    g5.metric("Gamma (Γ)", f"{gamma_val:,.6f}")
    g6.metric("Implied Volatility (IV)", f"{iv_val:,.2f}%")
    st.caption("*Note: Greeks (Delta, Theta, Gamma, IV) will show 0.00 for Futures. Type an Options symbol to see actual Greek values.*")

    st.divider()

    # --- STRATEGY CHECKLIST & LOGIC ---
    st.subheader("📋 Advanced Algorithmic Checklist")
    chk1, chk2, chk3, chk4 = st.columns(4)
    
    if current_sma > 0:
        chk1.info(f"📈 Trend Check: {'Bullish (>SMA)' if is_price_above_sma else 'Bearish (<SMA)'}")
    else:
        chk1.warning("⏳ Trend Loading...")
        
    if is_buyer_strong:
        chk2.success(f"💪 Volume Pressure: Buyers ({buy_pressure:.1f}%)")
    elif is_seller_strong:
        chk2.error(f"🩸 Volume Pressure: Sellers ({sell_pressure:.1f}%)")
    else:
        chk2.warning("⚖️ Volume Pressure: Neutral")

    # OI/Volume Quality Check
    if oi > 0 and volume > 0:
        chk3.success("🔥 High Liquidity (OI & Vol Present)")
    else:
        chk3.warning("⚠️ Low Liquidity (Wait)")

    # 🚨 FINAL SIGNAL CALCULATION
    signal = "WAIT ⏳"
    if current_sma > 0:
        if is_price_above_sma and is_buyer_strong and (oi > 0 or volume > 0):
            signal = "🟢 BUY LONG SIGNAL"
        elif not is_price_above_sma and is_seller_strong and (oi > 0 or volume > 0):
            signal = "🔴 SELL SHORT SIGNAL"
    
    chk4.metric("🎯 Bot Status", signal)

    st.divider()

    # --- DASHBOARD METRICS ---
    current_time = datetime.now().strftime("%I:%M:%S %p")
    st.caption(f"⚡ Live Market Data | Last Updated: {current_time}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Price (Orderbook)", f"${spot:,.2f}")
    
    if current_sma > 0:
        c2.metric("SMA Trend Line", f"${current_sma:,.2f}", delta=f"{round(spot-current_sma, 2)}")
    else:
        c2.metric("SMA Trend Line", "Loading...")
    
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

    # --- LIVE TRADE PANEL ---
    t1, t2 = st.columns(2)
    buy_clicked = t1.button("🟢 EXECUTE BUY LONG", use_container_width=True)
    sell_clicked = t2.button("🔴 EXECUTE SELL SHORT", use_container_width=True)

    if buy_clicked:
        try:
            ex.create_market_buy_order(ccxt_symbol, trade_qty)
            st.success(f"✅ Buy Order Placed Successfully for {ccxt_symbol}!")
        except Exception as e:
            st.error(f"❌ Trade Error: {e}")
            
    if sell_clicked:
        try:
            ex.create_market_sell_order(ccxt_symbol, trade_qty)
            st.success(f"✅ Sell Order Placed Successfully for {ccxt_symbol}!")
        except Exception as e:
            st.error(f"❌ Trade Error: {e}")

    # Refresh Loop (Auto-Reload)
    time.sleep(3)
    st.rerun()

except Exception as e:
    st.error(f"Data refresh ho raha hai... Error Details: {e}")
    time.sleep(4)
    st.rerun()
