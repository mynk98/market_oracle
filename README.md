# Lyra Market Oracle

Autonomous Wealth Architecture for the Indian Stock Market (NSE/BSE).

## Features
- **Daily Scanner:** Real-time technical analysis using RSI, MACD, and Bollinger Bands.
- **Sentiment Engine:** Scrapes global news to calculate market bias and correlate events.
- **Autonomous Paper Trading:** Starts with ₹1 Lakh and executes trades based on high-probability signals.
- **Self-Learning:** Updates RSI thresholds and logic recursively based on P&L and accuracy score.
- **Custom Analysis:** Analyze any ticker (e.g., `RELIANCE.NS` or BSE codes like `500325`).

## Quick Start

### 1. Initial Setup
Run the setup script to create a virtual environment and install dependencies:
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Run the Dashboard
Launch the visual interface:
```bash
chmod +x run.sh
./run.sh
```

## Directory Structure
- `scripts/`: Core logic for scanning, sentiment, and the dashboard.
- `data/`: Persistent storage for portfolio, history, news, and watchlist.
- `market_oracle/`: Root directory for the surveillance system.

## Requirements
- Python 3.9+
- Active internet connection (for Yahoo Finance and DuckDuckGo Search)
