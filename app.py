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

    # 🚨 NAYA AGGRESSIVE SIGNAL CALCULATION
    signal = "WAIT ⏳"
    
    # 1. PERFECT SNIPER SETUP (High Conviction - Sab kuch match ho raha hai)
    if is_trend_up and buy_pressure > 55 and funding_rate <= 0:
        signal = "🟢 SNIPER BUY (High Conviction)"
    elif is_trend_down and sell_pressure > 55 and funding_rate >= 0:
        signal = "🔴 SNIPER SELL (High Conviction)"
        
    # 2. TREND FOLLOWER SETUP (Agar Orderbook thoda bhi support kare toh trade le lo)
    elif is_trend_up and buy_pressure > 50:
        signal = "🟢 BUY LONG (Trend Follow)"
    elif is_trend_down and sell_pressure > 50:
        signal = "🔴 SELL SHORT (Trend Follow)"
        
    # 3. DANGER WARNINGS (Agar trend aur orderbook apas mein lad rahe hain)
    elif is_trend_up and sell_pressure > 60:
        signal = "⚠️ WAIT: Trend UP but Heavy Selling"
    elif is_trend_down and buy_pressure > 60:
        signal = "⚠️ WAIT: Trend DOWN but Heavy Buying"
    
    chk4.metric("🎯 Bot Final Signal", signal)
