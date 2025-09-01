#!/usr/bin/env python3
"""
Transfer stock data from Firestore to BigQuery
"""

import pandas as pd
from google.cloud import firestore
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime
import time

# 환경 변수
GOOGLE_SERVICE_ACCOUNT = "/Users/cg01-piwoo/my_quant/access_info/data/quantsungyong-663604552de9.json"
FIRESTORE_DATABASE_ID = "quant-data-etl"
FIRESTORE_COLLECTION = "stock_raw_data"
BIGQUERY_DATASET = "finviz_data"
BIGQUERY_TABLE = "stock_data"

# 처리할 티커 목록
tickers = [
    "AGQ", "AMZN", "BTAL", "EFNL", "ENIC", "ERX", "ERY", "EWG", "EWH", "EWO", "EWS",
    "FAS", "FAZ", "FEUZ", "FGM", "FLGR", "FXY", "GOOGL", "IDOG", "IVLU", "IWM", "KOLD", 
    "KSTR", "KTEC", "LDEM", "META", "MSFT", "NFLX", "NVDA", "ONEQ", "ROM", "RXD", "RXL", 
    "SCO", "SHLD", "SOXL", "SOXS", "SQQQ", "TAIL", "TBF", "TBT", "TBX", "TECL", "TECS", 
    "TQQQ", "TSLA", "TZA", "UBT", "UCC", "UCO", "UGE", "UGL", "UJB", "UNG", "URE", "UST", 
    "UXI", "UYG", "UYM", "VDE", "VXX", "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP",
    "XLRE", "XLV", "XPP", "YCS", "YINN", "ZSL"
]

def get_credentials():
    """인증 정보 생성"""
    return service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT,
        scopes=[
            "https://www.googleapis.com/auth/bigquery",
            "https://www.googleapis.com/auth/datastore"
        ]
    )

def get_firestore_data(ticker, credentials):
    """Firestore에서 티커 데이터 가져오기"""
    try:
        # Firestore 클라이언트
        db = firestore.Client(
            project=credentials.project_id,
            credentials=credentials,
            database=FIRESTORE_DATABASE_ID
        )
        
        # 문서 가져오기
        doc_ref = db.collection(FIRESTORE_COLLECTION).document(ticker)
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"❌ {ticker}: Firestore에 데이터 없음")
            return None
            
        data = doc.to_dict()
        
        if 'data' not in data:
            print(f"❌ {ticker}: 가격 데이터 없음")
            return None
            
        price_data = data['data']
        
        # DataFrame 생성
        df = pd.DataFrame({
            'ticker': ticker,
            'date': pd.to_datetime(price_data['dates']),
            'open': price_data['open'],
            'high': price_data['high'],
            'low': price_data['low'],
            'close': price_data['close'],
            'volume': price_data['volume']
        })
        
        return df
        
    except Exception as e:
        print(f"❌ {ticker}: Firestore 읽기 오류 - {str(e)}")
        return None

def create_bigquery_table_if_not_exists(client):
    """BigQuery 테이블이 없으면 생성"""
    dataset_ref = client.dataset(BIGQUERY_DATASET)
    table_ref = dataset_ref.table(BIGQUERY_TABLE)
    
    try:
        client.get_table(table_ref)
        print(f"✅ 테이블 {BIGQUERY_DATASET}.{BIGQUERY_TABLE}이 이미 존재합니다.")
    except:
        print(f"📦 테이블 {BIGQUERY_DATASET}.{BIGQUERY_TABLE}을 생성합니다.")
        schema = [
            bigquery.SchemaField("ticker", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("open", "FLOAT64"),
            bigquery.SchemaField("high", "FLOAT64"),
            bigquery.SchemaField("low", "FLOAT64"),
            bigquery.SchemaField("close", "FLOAT64"),
            bigquery.SchemaField("volume", "INT64"),
        ]
        table = bigquery.Table(table_ref, schema=schema)
        table = client.create_table(table)
        print(f"✅ 테이블 생성 완료")

def upload_to_bigquery(df, ticker, client):
    """DataFrame을 BigQuery에 업로드"""
    table_id = f"{client.project}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"
    
    # 기존 데이터 삭제 (해당 티커만)
    delete_query = f"""
    DELETE FROM `{table_id}`
    WHERE ticker = '{ticker}'
    """
    
    try:
        # 기존 데이터 삭제
        delete_job = client.query(delete_query)
        delete_job.result()
        
        # 새 데이터 업로드
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
            schema=[
                bigquery.SchemaField("ticker", "STRING"),
                bigquery.SchemaField("date", "DATE"),
                bigquery.SchemaField("open", "FLOAT64"),
                bigquery.SchemaField("high", "FLOAT64"),
                bigquery.SchemaField("low", "FLOAT64"),
                bigquery.SchemaField("close", "FLOAT64"),
                bigquery.SchemaField("volume", "INT64"),
            ]
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        
        return True
    except Exception as e:
        print(f"❌ BigQuery 업로드 오류: {str(e)}")
        return False

def main():
    """메인 실행 함수"""
    print(f"Firestore → BigQuery 데이터 전송 시작")
    print(f"총 {len(tickers)}개 티커 처리")
    print("=" * 60)
    
    # 인증 정보
    credentials = get_credentials()
    
    # BigQuery 클라이언트
    bq_client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    
    # 테이블 생성 확인
    create_bigquery_table_if_not_exists(bq_client)
    
    # 처리 통계
    success_count = 0
    failed_tickers = []
    total_records = 0
    
    # 배치 처리
    batch_size = 5
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        print(f"\n배치 #{batch_num} 처리 중 ({len(batch)}개)")
        print(f"티커: {', '.join(batch)}")
        
        for ticker in batch:
            # Firestore에서 데이터 가져오기
            df = get_firestore_data(ticker, credentials)
            
            if df is not None and not df.empty:
                # BigQuery에 업로드
                if upload_to_bigquery(df, ticker, bq_client):
                    success_count += 1
                    total_records += len(df)
                    print(f"✅ {ticker}: {len(df)}개 레코드 업로드 완료")
                else:
                    failed_tickers.append(ticker)
            else:
                failed_tickers.append(ticker)
        
        # 다음 배치 전 잠시 대기
        if i + batch_size < len(tickers):
            time.sleep(2)
    
    # 최종 결과
    print("\n" + "=" * 60)
    print("🏁 전송 완료!")
    print(f"성공: {success_count}개 티커")
    print(f"실패: {len(failed_tickers)}개 티커")
    print(f"총 레코드 수: {total_records:,}개")
    
    if failed_tickers:
        print(f"\n실패한 티커: {', '.join(failed_tickers)}")
    
    # 데이터 확인 쿼리
    print("\n📊 데이터 확인:")
    check_query = f"""
    SELECT 
        COUNT(DISTINCT ticker) as unique_tickers,
        COUNT(*) as total_records,
        MIN(date) as earliest_date,
        MAX(date) as latest_date
    FROM `{bq_client.project}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}`
    WHERE ticker IN ({','.join([f"'{t}'" for t in tickers])})
    """
    
    results = bq_client.query(check_query).result()
    for row in results:
        print(f"  - 티커 수: {row.unique_tickers}")
        print(f"  - 총 레코드: {row.total_records:,}")
        print(f"  - 기간: {row.earliest_date} ~ {row.latest_date}")

if __name__ == "__main__":
    main()