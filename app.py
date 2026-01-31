import streamlit as st
import ccxt
import pandas as pd
import time

st.set_page_config(page_title="Ultra-Fast Arbitrage Scanner", layout="wide")

st.title("⚡ Scanner Arbitraj Triunghiular")
st.sidebar.header("Setări")

# Selecție Exchange
ex_name = st.sidebar.selectbox("Alege Exchange-ul:", ['kraken', 'bybit', 'kucoin', 'okx', 'binance'])
base_currency = st.sidebar.selectbox("Moneda de bază:", ['USDT', 'BTC', 'ETH'])
min_profit = st.sidebar.slider("Profit minim detectat (%)", 0.0, 1.0, 0.1, step=0.01)

# Inițializare Exchange cu gestionare de erori
try:
    exchange = getattr(ccxt, ex_name)()
except:
    st.error("Exchange-ul selectat nu este suportat momentan.")
    st.stop()

def get_triangles(base):
    try:
        markets = exchange.load_markets()
        symbols = [s for s in markets if exchange.markets[s]['active']]
        triangles = []
        for s1 in symbols:
            if s1.endswith('/' + base):
                middle = s1.split('/')[0]
                for s2 in symbols:
                    if s2.startswith(middle + '/'):
                        end = s2.split('/')[1]
                        s3 = end + '/' + base
                        if s3 in symbols:
                            triangles.append([s1, s2, s3])
        return triangles
    except Exception as e:
        return []

triangles = get_triangles(base_currency)

if not triangles:
    st.warning(f"⚠️ Nu se pot prelua date de pe {ex_name}. Probabil serverul este restricționat geografic de acest exchange. Încearcă Kraken sau Bybit.")
else:
    st.sidebar.success(f"S-au găsit {len(triangles)} combinații.")

placeholder = st.empty()

while True:
    try:
        tickers = exchange.fetch_tickers()
        results = []

        for t in triangles:
            if t[0] in tickers and t[1] in tickers and t[2] in tickers:
                p1 = tickers[t[0]]['ask']
                p2 = tickers[t[1]]['ask']
                p3 = tickers[t[2]]['bid']

                if p1 and p2 and p3 and p1 > 0 and p2 > 0:
                    final_amount = (1 / p1 / p2) * p3
                    profit_pct = (final_amount - 1) * 100

                    if profit_pct > min_profit:
                        results.append({
                            "Drum Arbitraj": f"{t[0]} ➔ {t[1]} ➔ {t[2]}",
                            "Profit Brut (%)": round(profit_pct, 4)
                        })

        with placeholder.container():
            if results:
                df = pd.DataFrame(results).sort_values(by="Profit Brut (%)", ascending=False)
                st.success(f"Oportunități live pe {ex_name.upper()}")
                st.table(df)
            else:
                st.info(f"Se scanează {ex_name}... Nicio oportunitate peste {min_profit}% momentan.")
        
    except Exception as e:
        # Aici "ascundem" eroarea urâtă și afișăm un mesaj prietenos
        with placeholder.container():
            st.error(f"Eroare de conexiune cu {ex_name}. Motiv: Restricție geografică sau API limitat. Încearcă alt exchange din listă.")
    
    time.sleep(2)