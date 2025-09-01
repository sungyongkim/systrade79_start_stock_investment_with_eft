#!/usr/bin/env python3
"""
Upload 10 years of stock data for specific tickers to Firestore via API
"""

import requests
import json
import time
from datetime import datetime

# API 엔드포인트
API_URL = "https://dir-ii-get-stockdata-of-newtickers-wmqm7agonq-du.a.run.app/refresh-tickers"

# 티커 목록
tickers = [
    "AGQ", "AMZN", "BTAL", "EFNL", "ENIC", "ERX", "ERY", "EWG", "EWH", "EWO", "EWS",
    "FAS", "FAZ", "FEUZ", "FGM", "FLGR", "FXY", "GOOGL", "IDOG", "IVLU", "IWM", "KOLD", 
    "KSTR", "KTEC", "LDEM", "META", "MSFT", "NFLX", "NVDA", "ONEQ", "ROM", "RXD", "RXL", 
    "SCO", "SHLD", "SOXL", "SOXS", "SQQQ", "TAIL", "TBF", "TBT", "TBX", "TECL", "TECS", 
    "TQQQ", "TSLA", "TZA", "UBT", "UCC", "UCO", "UGE", "UGL", "UJB", "UNG", "URE", "UST", 
    "UXI", "UYG", "UYM", "VDE", "VXX", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP",
    "XLRE", "XLV", "XPP", "YCS", "YINN", "ZSL"
]

def upload_batch(batch_tickers, batch_num):
    """배치 단위로 티커 데이터 업로드"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    message_id = f"batch_{batch_num}_{timestamp}"
    
    payload = {
        "message_id": message_id,
        "refresh_tickers": batch_tickers,
        "metadata": {
            "period": "10y",  # 10년치 데이터
            "interval": "1d",
            "preset_name": "backtest_10y_data"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token-123"
    }
    
    try:
        print(f"\n배치 #{batch_num} 처리 중 ({len(batch_tickers)}개 티커)")
        print(f"티커: {', '.join(batch_tickers)}")
        
        response = requests.post(API_URL, json=payload, headers=headers, timeout=600)
        
        if response.status_code == 200:
            result = response.json()
            success = result.get('results', {}).get('success', 0)
            failed = result.get('results', {}).get('failed', 0)
            print(f"✅ 배치 #{batch_num} 완료: 성공 {success}개, 실패 {failed}개")
            
            # 실패한 티커 확인
            if failed > 0:
                details = result.get('details', [])
                failed_tickers = [d['ticker'] for d in details if d['status'] == 'failed']
                if failed_tickers:
                    print(f"❌ 실패한 티커: {', '.join(failed_tickers)}")
                    
            return True
        else:
            print(f"❌ 배치 #{batch_num} 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️ 배치 #{batch_num} 타임아웃")
        return False
    except Exception as e:
        print(f"❌ 배치 #{batch_num} 오류: {str(e)}")
        return False

def main():
    """메인 실행 함수"""
    print(f"총 {len(tickers)}개 티커의 10년치 데이터를 Firestore에 저장합니다.")
    print("=" * 60)
    
    # 배치 크기 설정 (API 안정성을 위해 5개씩)
    batch_size = 5
    total_batches = (len(tickers) + batch_size - 1) // batch_size
    
    success_count = 0
    failed_batches = []
    
    # 배치 처리
    for i in range(0, len(tickers), batch_size):
        batch_num = (i // batch_size) + 1
        batch = tickers[i:i + batch_size]
        
        # 배치 업로드
        if upload_batch(batch, batch_num):
            success_count += 1
        else:
            failed_batches.append(batch_num)
        
        # 마지막 배치가 아니면 대기
        if batch_num < total_batches:
            wait_time = 5
            print(f"다음 배치까지 {wait_time}초 대기...")
            time.sleep(wait_time)
    
    # 최종 결과
    print("\n" + "=" * 60)
    print("🏁 처리 완료!")
    print(f"총 배치: {total_batches}개")
    print(f"성공: {success_count}개")
    print(f"실패: {len(failed_batches)}개")
    
    if failed_batches:
        print(f"\n실패한 배치 번호: {failed_batches}")
        print("\n실패한 티커들을 다시 시도하려면 다음 티커들을 확인하세요:")
        for batch_num in failed_batches:
            start_idx = (batch_num - 1) * batch_size
            end_idx = min(start_idx + batch_size, len(tickers))
            failed_tickers = tickers[start_idx:end_idx]
            print(f"배치 #{batch_num}: {failed_tickers}")

if __name__ == "__main__":
    main()