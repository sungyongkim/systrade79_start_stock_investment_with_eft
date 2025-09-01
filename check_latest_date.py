#!/usr/bin/env python3
"""
Check the latest date in BigQuery backtest_test table
"""

from google.cloud import bigquery
from google.oauth2 import service_account

# 환경 변수에서 서비스 계정 파일 경로 가져오기
GOOGLE_SERVICE_ACCOUNT = "/Users/cg01-piwoo/my_quant/access_info/data/quantsungyong-663604552de9.json"

# BigQuery 설정
DATASET_ID = "finviz_data"
TABLE_ID = "backtest_test"

def get_bigquery_client():
    """BigQuery 클라이언트 생성"""
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT,
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    return bigquery.Client(credentials=credentials, project=credentials.project_id)

def main():
    """메인 실행 함수"""
    # BigQuery 클라이언트 생성
    client = get_bigquery_client()
    
    # 가장 최근 날짜 확인 쿼리
    query = f"""
    SELECT 
        MAX(date) as latest_date,
        MIN(date) as earliest_date,
        COUNT(DISTINCT date) as unique_dates,
        COUNT(DISTINCT ticker) as unique_tickers
    FROM `{client.project}.{DATASET_ID}.{TABLE_ID}`
    """
    
    print("테이블 날짜 정보 확인 중...")
    results = client.query(query).result()
    
    for row in results:
        print(f"\n📊 테이블: {DATASET_ID}.{TABLE_ID}")
        print(f"가장 최근 날짜: {row.latest_date}")
        print(f"가장 오래된 날짜: {row.earliest_date}")
        print(f"고유 날짜 수: {row.unique_dates}")
        print(f"티커 수: {row.unique_tickers}")
    
    # 최근 날짜의 데이터 샘플 확인
    latest_date_query = f"""
    SELECT 
        date,
        ticker,
        close,
        volume
    FROM `{client.project}.{DATASET_ID}.{TABLE_ID}`
    WHERE date = (SELECT MAX(date) FROM `{client.project}.{DATASET_ID}.{TABLE_ID}`)
    ORDER BY ticker
    LIMIT 10
    """
    
    print(f"\n최근 날짜 데이터 샘플:")
    print("-" * 60)
    print(f"{'Date':<12} {'Ticker':<10} {'Close':>10} {'Volume':>15}")
    print("-" * 60)
    
    for row in client.query(latest_date_query):
        print(f"{str(row.date):<12} {row.ticker:<10} {row.close:>10.2f} {row.volume:>15,}")

if __name__ == "__main__":
    main()