import os
import json
import datetime
import yfinance as yf # Standard for fetching market data

def fetch_market_pulse():
    """Fetches basic data for Indian Market Indices and key commodities."""
    # NSE and BSE Indices
    tickers = {
        "NIFTY_50": "^NSEI",
        "SENSEX": "^BSESN",
        "SILVER_MCX": "SILVER1!", # Typical MCX Future ticker on many platforms
        "MCX_STOCK": "MCX.NS"    # Multi Commodity Exchange of India Ltd.
    }
    
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "market_status": "Closed" if datetime.datetime.now().hour > 15 or datetime.datetime.now().hour < 9 else "Open",
        "data": {}
    }

    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if not hist.empty:
                last_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = ((last_price - prev_price) / prev_price) * 100
                report["data"][name] = {
                    "price": round(last_price, 2),
                    "change_pct": round(change, 2),
                    "trend": "Up" if change > 0 else "Down"
                }
        except Exception as e:
            report["data"][name] = {"error": str(e)}
            
    return report

if __name__ == "__main__":
    pulse = fetch_market_pulse()
    output_path = "market_oracle/data/daily_pulse.json"
    with open(output_path, "w") as f:
        json.dump(pulse, f, indent=2)
    print(f"Market Pulse saved to {output_path}")
