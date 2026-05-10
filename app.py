import streamlit as st
import ccxt
import json

# --- YAHAN APNI KEYS DAALEIN ---
API_KEY = "YAHAN_APNI_API_KEY_PASTE_KAREIN"
SECRET_KEY = "YAHAN_APNI_SECRET_KEY_PASTE_KAREIN"

st.set_page_config(page_title="Data Spy", layout="wide")

@st.cache_resource
def get_exchange():
    return ccxt.delta({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
        'options': {'defaultType': 'future'}
    })

st.title("🕵️‍♂️ Delta Data Spy")

st.sidebar.header("Check Data")
test_symbol = st.sidebar.text_input("Enter Symbol to Test", value="BTC/USDT:USDT")

if st.sidebar.button("Fetch Raw Data"):
    try:
        ex = get_exchange()
        ticker = ex.fetch_ticker(test_symbol)
        
        st.subheader(f"Raw Ticker Data for {test_symbol}")
        
        # Data ko sundar (JSON format) tarike se dikhane ke liye
        st.json(ticker)
        
        st.divider()
        
        # Sirf 'info' wala hissa nikal kar dikhayenge
        info_data = ticker.get('info', {})
        st.subheader("Sirf 'info' wala data:")
        st.json(info_data)
        
        st.divider()
        
        # Sirf 'greeks' wala hissa nikal kar dikhayenge
        greeks_data = info_data.get('greeks', {})
        st.subheader("Sirf 'greeks' wala data:")
        if greeks_data:
             st.json(greeks_data)
        else:
             st.error("Is symbol ke liye koi 'greeks' data nahi aaya (Null hai).")
             
    except Exception as e:
        st.error(f"Error fetching data: {e}")
