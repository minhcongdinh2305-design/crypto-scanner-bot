#!/usr/bin/env python3
"""
Test Suite for Binance API Data Fetching & Indicator Calculation
Command: python3 test_fetch.py
"""
import sys
from binance_api import get_ticker_24h, get_klines, fetch_multi_klines_parallel
from scanner import get_coin_report

def main():
    print("=" * 60)
    print("🧪 TESTING BINANCE DATA FETCHING & TA ENGINE")
    print("=" * 60)
    
    test_coins = ["BTC", "LINK", "ETH", "SOL"]
    
    for coin in test_coins:
        print(f"\n⏳ Testing {coin}/USDT...")
        ticker = get_ticker_24h(coin)
        if ticker:
            print(f"✅ 24h Ticker OK: Price = {ticker['lastPrice']}, Change = {ticker['priceChangePercent']}%")
        else:
            print(f"❌ 24h Ticker Failed for {coin}")
            
        candles = get_klines(coin, "1h", 200)
        print(f"📊 1h Klines Count: {len(candles)} candles")
        
        report = get_coin_report(coin)
        print(f"\n--- REPORT FOR {coin} ---")
        print(report)
        print("-" * 40)

if __name__ == "__main__":
    main()
