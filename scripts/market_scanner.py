import yfinance as yf
import pandas as pd
import pandas_ta as ta
import json
import os
import datetime
import re
import sys
from nsepython import nse_eq

# --- Configuration ---
BASE_DIR = "/Users/abhisheksonkar/Project/gemini personality"
DATA_DIR = os.path.join(BASE_DIR, "market_oracle/data")
SCAN_RESULTS_FILE = os.path.join(DATA_DIR, "scan_results.json")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.json")
PREDICTION_LOG_FILE = os.path.join(DATA_DIR, "prediction_log.json")
HISTORY_FILE = os.path.join(DATA_DIR, "historical_predictions.json")
LATEST_NEWS_FILE = os.path.join(DATA_DIR, "latest_news.json")
WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")

STARTING_CASH = 100000.0
DEFAULT_TICKERS = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "SBIN.NS", "MCX.NS", "SILVERBEES.NS", "BSE.NS"]

def load_json(file_path, default=None):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except: return default
    return default

def save_json(data, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

def get_news_sentiment():
    news = load_json(LATEST_NEWS_FILE)
    if not news or 'categories' not in news: return 0
    score = 0
    text_blob = ""
    for items in news['categories'].values():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    text_blob += f" {item.get('title', '')} {item.get('snippet', '')}".lower()
    pos = ['surge', 'growth', 'bullish', 'profit', 'high', 'recovery', 'stable', 'uptick']
    neg = ['drop', 'crash', 'bearish', 'loss', 'war', 'crisis', 'decline', 'inflation']
    for w in pos: score += len(re.findall(w, text_blob))
    for w in neg: score -= len(re.findall(w, text_blob))
    return round(max(-15, min(15, score / 3)), 2)

def get_fundamental_score(symbol):
    """Calculates a fundamental score (0-100) using yfinance and nsepython."""
    try:
        # 1. Clean symbol for NSE
        clean_sym = symbol.replace(".NS", "")
        
        # 2. Get Sector PE from NSE
        sector_pe = 20 # Default
        try:
            meta = nse_eq(clean_sym).get('metadata', {})
            sector_pe = meta.get('pdSectorPe', 20)
        except: pass
        
        # 3. Get Key Metrics from yfinance
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        pe = info.get('forwardPE') or info.get('trailingPE') or 30
        roe = info.get('returnOnEquity', 0)
        debt_to_eq = info.get('debtToEquity', 0) / 100 # yf often returns 100 for 1.0
        div_yield = info.get('dividendYield', 0)
        
        f_score = 50 # Start at neutral
        
        # Valuation logic
        if pe < sector_pe: f_score += 15
        elif pe > sector_pe * 1.5: f_score -= 10
        
        # Profitability logic
        if roe > 0.15: f_score += 15 # > 15% ROE is good
        elif roe < 0.05: f_score -= 10
        
        # Risk logic
        if debt_to_eq < 1.0: f_score += 10
        elif debt_to_eq > 2.0: f_score -= 15
        
        # Dividend logic
        if div_yield > 0.02: f_score += 10
        
        return {
            "score": max(0, min(100, f_score)),
            "pe": round(pe, 2),
            "sector_pe": round(sector_pe, 2),
            "roe_pct": round(roe * 100, 2),
            "debt_to_equity": round(debt_to_eq, 2)
        }
    except:
        return {"score": 50, "pe": "N/A", "sector_pe": "N/A", "roe_pct": "N/A", "debt_to_equity": "N/A"}

def analyze_ticker(symbol, rsi_buy_thresh, rsi_sell_thresh, sentiment_bias):
    try:
        if symbol.isdigit(): symbol = f"{symbol}.BO"
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if len(df) < 30: return None
            
        df.ta.rsi(append=True)
        df.ta.macd(append=True)
        df.ta.bbands(append=True)
        
        cols = df.columns
        bb_upper_col = [c for c in cols if 'BBU' in c][0]
        bb_lower_col = [c for c in cols if 'BBL' in c][0]
        rsi_col = [c for c in cols if 'RSI' in c][0]
        macd_col = [c for c in cols if 'MACD_' in c and not 's_' in c and not 'h_' in c][0]
        macds_col = [c for c in cols if 'MACDs_' in c][0]
        
        last_row = df.iloc[-1]
        price = round(last_row['Close'], 2)
        rsi = last_row[rsi_col]
        macd = last_row[macd_col]
        macd_s = last_row[macds_col]
        
        # Technical Score (0-100)
        t_score = 50
        if rsi < rsi_buy_thresh: t_score += 25
        elif rsi > rsi_sell_thresh: t_score -= 25
        if macd > macd_s: t_score += 10
        else: t_score -= 10
        
        # Fundamental Score
        f_data = get_fundamental_score(symbol)
        f_score = f_data['score']
        
        # Master Oracle Score
        # 40% Technical, 30% Sentiment, 30% Fundamental
        master_score = (t_score * 0.4) + (50 + sentiment_bias * 2) * 0.3 + (f_score * 0.3)
        
        action = "HOLD"
        if master_score > 65: action = "BUY"
        elif master_score < 35: action = "SELL"

        priority = "HIGH" if master_score >= 75 or master_score <= 25 else "MEDIUM" if master_score >= 60 or master_score <= 40 else "LOW"
        
        target_price = round(last_row[bb_upper_col] if action == "BUY" else price * 0.95, 2)
        stop_loss = round(last_row[bb_lower_col] if action == "BUY" else price * 1.05, 2)
        if action == "BUY" and target_price <= price: target_price = round(price * 1.05, 2)
        if action == "SELL" and target_price >= price: target_price = round(price * 0.95, 2)
        
        profit_pct = round(((target_price - price) / price) * 100, 2) if action == "BUY" else round(((price - target_price) / price) * 100, 2)
        loss_pct = round(((price - stop_loss) / price) * 100, 2) if action == "BUY" else round(((stop_loss - price) / price) * 100, 2)

        return {
            "symbol": symbol,
            "name": ticker.info.get('shortName', symbol),
            "price": price,
            "action": action,
            "priority": priority,
            "rsi": round(rsi, 2),
            "score": round(master_score, 2),
            "fundamentals": f_data,
            "potential_profit_pct": max(0, profit_pct),
            "potential_loss_pct": max(0, loss_pct),
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}", file=sys.stderr)
        return None

def run_pipeline(custom_tickers=None):
    python_exe = sys.executable
    os.system(f'"{python_exe}" "{os.path.join(os.path.dirname(__file__), "sentiment_engine.py")}" > /dev/null 2>&1')
    
    sentiment_bias = get_news_sentiment()
    portfolio = load_json(PORTFOLIO_FILE, {"cash": 100000.0, "invested": 0.0, "total_value": 100000.0, "holdings": {}, "total_profit_loss": 0.0, "trade_history": []})
    pred_log = load_json(PREDICTION_LOG_FILE, {"buy_rsi_threshold": 30.0, "sell_rsi_threshold": 70.0, "accuracy_score": 50.0})
    
    target_tickers = custom_tickers if custom_tickers else load_json(WATCHLIST_FILE, DEFAULT_TICKERS)
    current_scan = [res for s in target_tickers if (res := analyze_ticker(s, pred_log["buy_rsi_threshold"], pred_log["sell_rsi_threshold"], sentiment_bias))]
    
    if not custom_tickers:
        history = load_json(HISTORY_FILE, [])
        history.append({"date": datetime.datetime.now().isoformat(), "predictions": current_scan, "sentiment_bias": sentiment_bias})
        save_json(history[-10:], HISTORY_FILE)
        
        holdings = portfolio.get("holdings", {})
        cash = portfolio.get("cash", STARTING_CASH)
        trade_history = portfolio.get("trade_history", [])
        
        for symbol, h in list(holdings.items()):
            curr = next((x for x in current_scan if x["symbol"] == symbol), None)
            if not curr: continue
            if curr["action"] == "SELL" or curr["price"] < h["avg_price"] * 0.95 or curr["price"] > h["avg_price"] * 1.15:
                val = h["qty"] * curr["price"]
                cash += val
                trade_history.append({"date": datetime.datetime.now().isoformat(), "type": "SELL", "symbol": symbol, "qty": h["qty"], "price": curr["price"], "profit": round(val - (h["qty"] * h["avg_price"]), 2)})
                del holdings[symbol]

        for item in current_scan:
            if item["action"] == "BUY" and item["priority"] == "HIGH" and item["symbol"] not in holdings:
                alloc = cash * 0.20
                if alloc > 2000:
                    qty = int(alloc / item["price"])
                    if qty > 0:
                        cash -= (qty * item["price"])
                        holdings[item["symbol"]] = {"qty": qty, "avg_price": item["price"], "date_bought": datetime.datetime.now().isoformat()}
                        trade_history.append({"date": datetime.datetime.now().isoformat(), "type": "BUY", "symbol": item["symbol"], "qty": qty, "price": item["price"]})

        current_inv = sum(h['qty']*next((x['price'] for x in current_scan if x['symbol']==s), h['avg_price']) for s, h in holdings.items())
        portfolio.update({"cash": round(cash, 2), "invested": round(current_inv, 2), "total_value": round(cash + current_inv, 2), "holdings": holdings, "total_profit_loss": round((cash + current_inv) - STARTING_CASH, 2), "trade_history": trade_history})
        
        save_json(current_scan, SCAN_RESULTS_FILE)
        save_json(portfolio, PORTFOLIO_FILE)
        save_json(pred_log, PREDICTION_LOG_FILE)
        
    return current_scan

if __name__ == "__main__":
    if len(sys.argv) > 1:
        results = run_pipeline(custom_tickers=sys.argv[1:])
        print(json.dumps(results, indent=2))
    else:
        run_pipeline()
