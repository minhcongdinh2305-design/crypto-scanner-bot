#!/usr/bin/env python3
"""
Direct Terminal Quantitative Verification Test
Command: python3 test_quantitative.py
"""
from scanner import get_coin_report

def main():
    print("=" * 60)
    print("🧪 QUANTITATIVE BOUNDARY FILTER VERIFICATION TEST")
    print("=" * 60)
    
    test_coins = ["BTC", "ETH", "SOL", "LINK"]
    
    for coin in test_coins:
        print(f"\n--- TESTING {coin} REPORT ---")
        report = get_coin_report(coin)
        print(report)
        print("-" * 40)

if __name__ == "__main__":
    main()
