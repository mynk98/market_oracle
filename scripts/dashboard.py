import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
import sys

st.set_page_config(page_title="Lyra Market Oracle", layout="wide")

# --- Configuration (Relative Paths) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
SCAN_FILE = os.path.join(DATA_DIR, "scan_results.json")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.json")
PRED_LOG_FILE = os.path.join(DATA_DIR, "prediction_log.json")
NEWS_FILE = os.path.join(DATA_DIR, "latest_news.json")
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")

def load_json(path, default=None):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default

def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def main():
    st.title("🌌 Lyra Market Oracle: Autonomous Wealth Architecture")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📡 Daily Scanner", "💼 Portfolio & Trades", "🧠 Model Evolution", "📰 Current Affairs", "🔍 Custom Analysis"])
    
    scan_data = load_json(SCAN_FILE)
    portfolio = load_json(PORTFOLIO_FILE)
    pred_log = load_json(PRED_LOG_FILE)
    news_data = load_json(NEWS_FILE)
    watchlist = load_json(WATCHLIST_FILE, ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "MCX.NS", "SILVERBEES.NS"])

    python_exe = sys.executable
    scanner_script = os.path.join(SCRIPT_DIR, "market_scanner.py")

    # --- TAB 1: SCANNER ---
    with tab1:
        if scan_data:
            df = pd.DataFrame(scan_data)
            st.subheader("🎯 High-Probability Targets (Main Watchlist)")
            buys = df[df['action'] == 'BUY'].sort_values('score', ascending=False)
            sells = df[df['action'] == 'SELL'].sort_values('score', ascending=False)
            
            c1, c2 = st.columns(2)
            with c1:
                st.success("🟢 RECOMMENDED BUYS")
                if not buys.empty:
                    st.dataframe(buys[['symbol', 'price', 'priority', 'potential_profit_pct']], width="stretch")
                else: st.write("No strong buy signals.")
            with c2:
                st.error("🔴 RECOMMENDED SELLS")
                if not sells.empty:
                    st.dataframe(sells[['symbol', 'price', 'priority', 'potential_loss_pct']], width="stretch")
                else: st.write("No urgent sell signals.")
                
            st.divider()
            st.subheader("📊 Full Market Overview")
            st.dataframe(df[['symbol', 'name', 'price', 'action', 'priority', 'rsi', 'score']], width="stretch")
            
            if st.button("🔄 Trigger Market & News Sync"):
                os.system(f'"{python_exe}" "{scanner_script}"')
                st.rerun()
        else:
            st.info("Run the scanner to see daily signals.")

    # --- TAB 2: PORTFOLIO ---
    with tab2:
        if portfolio:
            val = portfolio['total_value']
            pl = portfolio['total_profit_loss']
            m1, m2, m3 = st.columns(3)
            m1.metric("Current Value", f"₹{val:,.2f}", delta=f"₹{pl:,.2f}")
            m2.metric("Cash", f"₹{portfolio['cash']:,.2f}")
            m3.metric("Invested", f"₹{portfolio['invested']:,.2f}")
            
            st.subheader("📦 Active Holdings")
            holdings = portfolio.get('holdings', {})
            if holdings:
                h_data = []
                for s, d in holdings.items():
                    curr_p = next((x['price'] for x in (scan_data or []) if x['symbol']==s), d['avg_price'])
                    h_data.append({"Symbol": s, "Qty": d['qty'], "Avg Price": d['avg_price'], "Curr Price": curr_p, "P&L": round((curr_p - d['avg_price'])*d['qty'], 2)})
                st.dataframe(pd.DataFrame(h_data), width="stretch")
            else: st.info("No active holdings.")
            
            st.subheader("📜 Trade History")
            hist = portfolio.get('trade_history', [])
            if hist:
                st.dataframe(pd.DataFrame(hist).sort_values('date', ascending=False), width="stretch")
        else: st.warning("Portfolio not initialized.")

    # --- TAB 3: BRAIN ---
    with tab3:
        if pred_log:
            st.subheader("📈 Learning Progress")
            acc = pred_log.get('accuracy_score', 50)
            st.metric("Model Prediction Accuracy", f"{acc}%")
            st.write(f"- **Buy RSI Threshold:** {pred_log.get('buy_rsi_threshold'):.2f}")
            st.write(f"- **Sell RSI Threshold:** {pred_log.get('sell_rsi_threshold'):.2f}")

    # --- TAB 4: NEWS ---
    with tab4:
        if news_data:
            st.subheader("🌍 Latest Global & Market News")
            for category, items in news_data['categories'].items():
                with st.expander(f"📌 {category.upper()} NEWS"):
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                st.markdown(f"**{item.get('title', 'No Title')}**")
                                st.write(item.get('snippet', ''))
                                st.caption(f"Source: {item.get('source', 'Unknown')} | [Link]({item.get('url', '#')})")
                                st.divider()
                    else: st.error(f"Error: {items}")
        else: st.info("No news data found.")

    # --- TAB 5: CUSTOM ANALYSIS ---
    with tab5:
        st.subheader("🔍 Analyze Any Stock (NSE/BSE)")
        new_ticker = st.text_input("Ticker Symbol", placeholder="e.g. TCS.NS or 500325")
        if st.button("Analyze Now"):
            if new_ticker:
                with st.spinner(f"Analyzing {new_ticker}..."):
                    import subprocess
                    result = subprocess.run([python_exe, scanner_script, new_ticker], capture_output=True, text=True)
                    try:
                        res_data = json.loads(result.stdout)
                        if res_data:
                            item = res_data[0]
                            color = "green" if item['action'] == "BUY" else "red" if item['action'] == "SELL" else "white"
                            st.markdown(f"""
                                <div style="padding: 20px; border: 2px solid {color}; border-radius: 10px; background: #111;">
                                    <h2 style="margin:0;">{item['name']} ({item['symbol']})</h2>
                                    <h1 style="color:{color}; margin:0;">{item['action']}</h1>
                                    <p>Priority: <b>{item['priority']}</b> | RSI: {item['rsi']}</p>
                                    <p style="color:#4CAF50;">Potential Profit: <b>+{item['potential_profit_pct']}%</b></p>
                                    <p style="color:#F44336;">Risk: <b>-{item['potential_loss_pct']}%</b></p>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button("➕ Add to Main Watchlist"):
                                if item['symbol'] not in watchlist:
                                    watchlist.append(item['symbol'])
                                    save_json(watchlist, WATCHLIST_FILE)
                                    st.success(f"Added {item['symbol']} to watchlist.")
                        else: st.error("No data found for this ticker.")
                    except: st.error("Analysis failed. Verify the ticker symbol.")

if __name__ == "__main__":
    main()
