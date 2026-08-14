#!/usr/bin/env python3
"""
CLI Test Suite for Crypto Scanner Bot
Run this file directly in terminal to test indicators & scan markets right now!
Command: python3 cli_test.py
"""
import sys
from scanner import get_coin_report, scan_market

def main():
    print("=" * 60)
    print("🤖 CHƯƠNG TRÌNH DÙNG THỬ BOT PHÂN TÍCH CHỈ BÁO CRYPTO")
    print("=" * 60)
    print("Dữ liệu trực tiếp từ Binance REST API (Miễn phí 100%)\n")
    
    while True:
        print("\nCHỌN CHỨC NĂNG:")
        print("1. Kiểm tra 1 Coin (Ví dụ: BTC, ETH, SOL, NEAR...)")
        print("2. Quét nhanh Top 15 Coin (Tìm tín hiệu Quá bán / Golden Cross)")
        print("3. Thoát (Exit)")
        
        choice = input("\n👉 Nhập lựa chọn (1/2/3): ").strip()
        
        if choice == "1":
            coin = input("👉 Nhập mã Coin (Ví dụ: BTC, ETH, SOL): ").strip().upper()
            if not coin:
                coin = "BTC"
            print(f"\n⏳ Đang tải dữ liệu và tính toán chỉ báo cho {coin}...\n")
            report = get_coin_report(coin)
            print(report)
        elif choice == "2":
            print("\n⏳ Đang quét Top 15 Coin trên thị trường (Binance)... Vui lòng chờ 3-5 giây...\n")
            report = scan_market()
            print(report)
        elif choice == "3" or choice.lower() == "exit":
            print("\n👋 Cảm ơn bạn đã sử dụng Bot! Hẹn gặp lại.")
            break
        else:
          print("\n❌ Lựa chọn không hợp lệ, vui lòng thử lại!")

if __name__ == "__main__":
    main()
