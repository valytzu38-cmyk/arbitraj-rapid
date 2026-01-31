import streamlit as st
import ccxt
import pandas as pd
import time

st.set_page_config(page_title="Ultra-Fast Arbitrage Scanner", layout="wide")

st.title("⚡ Scanner Arbitraj Triunghiular Live")
st.sidebar.header("Setări")

# 1. Selecție Exchange
ex_name = st.sidebar.selectbox("Alege Exchange-ul:", ['binance', 'kraken', 'kucoin', 'okx', 'bybit'])
base_currency = st.sidebar.selectbox("Moneda de bază:", ['USDT', 'BTC', 'ETH'])
min_profit = st.sidebar.slider("Profit minim detectat (%)", 0.0, 1.0, 0.1, step=0.01)

# Inițializare Exchange
exchange = getattr(ccxt, ex_name)()

def get_triangles(base):
    try:
        markets = exchange.load_markets()
        symbols = [s for s in markets if exchange.markets[s]['active']]
        
        # Găsim perechile care încep cu moneda de bază (ex: BTC/USDT)
        triangles = []
        for s1 in symbols:
            if s1.endswith('/' + base):
                middle = s1.split('/')[0] # ex: BTC
                for s2 in symbols:
                    if s2.startswith(middle + '/'):
                        end = s2.split('/')[1] # ex: ETH
                        s3 = end + '/' + base
                        if s3 in symbols:
                            triangles.append([s1, s2, s3])
        return triangles
    except:
        return []

triangles = get_triangles(base_currency)
st.sidebar.write(f"S-au găsit {len(triangles)} combinații posibile.")

placeholder = st.empty()

# Rularea în buclă pentru viteză maximă
while True:
    try:
        # Preluăm toate prețurile dintr-o singură cerere (mult mai rapid)
        tickers = exchange.fetch_tickers()
        results = []

        for t in triangles:
            p1 = tickers[t[0]]['ask'] # Cumperi prima monedă
            p2 = tickers[t[1]]['ask'] # Cumperi a doua monedă
            p3 = tickers[t[2]]['bid'] # Vinzi înapoi în moneda de bază

            if p1 and p2 and p3 and p1 > 0 and p2 > 0:
                # Calcul profit: începi cu 1 unitate
                # Pas 1: Base -> Middle (1 / p1)
                # Pas 2: Middle -> End ((1/p1) / p2)
                # Pas 3: End -> Base (((1/p1) / p2) * p3)
                final_amount = (1 / p1 / p2) * p3
                profit_pct = (final_amount - 1) * 100

                if profit_pct > min_profit:
                    results.append({
                        "Perechi": f"{t[0]} ➔ {t[1]} ➔ {t[2]}",
                        "Profit (%)": round(profit_pct, 4),
                        "Ultimul Update": time.strftime('%H:%M:%S')
                    })

        with placeholder.container():
            if results:
                df = pd.DataFrame(results).sort_values(by="Profit (%)", ascending=False)
                st.success(f"Oportunități găsite pe {ex_name.upper()}")
                st.table(df)
            else:
                st.info("Nicio oportunitate profitabilă momentan. Se scanează...")

    except Exception as e:
        st.error(f"Eroare la conectare: {e}")
    
    time.sleep(1) # Refresh la fiecare secundă
