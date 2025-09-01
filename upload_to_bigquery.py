#!/usr/bin/env python3
"""
Upload adx_only*.csv files to BigQuery
"""

import os
import glob
import pandas as pd
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

def create_table_schema():
    """테이블 스키마 정의"""
    schema = [
        bigquery.SchemaField("ticker", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("open", "FLOAT64"),
        bigquery.SchemaField("high", "FLOAT64"),
        bigquery.SchemaField("low", "FLOAT64"),
        bigquery.SchemaField("close", "FLOAT64"),
        bigquery.SchemaField("volume", "INT64"),
        bigquery.SchemaField("atr", "FLOAT64"),
        bigquery.SchemaField("adx_14", "FLOAT64"),
        bigquery.SchemaField("pdi_14", "FLOAT64"),
        bigquery.SchemaField("mdi_14", "FLOAT64"),
        bigquery.SchemaField("chaikin_oscillator", "FLOAT64"),
        bigquery.SchemaField("chaikin_signal", "FLOAT64"),
        bigquery.SchemaField("stochastic_k_line", "FLOAT64"),
        bigquery.SchemaField("stochastic_d_line", "FLOAT64"),
        bigquery.SchemaField("macd_line", "FLOAT64"),
        bigquery.SchemaField("macd_9_signal_line", "FLOAT64"),
        bigquery.SchemaField("macd_histogram", "FLOAT64"),
        bigquery.SchemaField("macd_signals", "STRING"),
        bigquery.SchemaField("obv_values", "INT64"),
        bigquery.SchemaField("obv_9_ma", "FLOAT64"),
        bigquery.SchemaField("obv_signals", "STRING"),
        bigquery.SchemaField("chaikin_yesterday", "FLOAT64"),
        bigquery.SchemaField("prev_range", "FLOAT64"),
        bigquery.SchemaField("target_price", "FLOAT64"),
        bigquery.SchemaField("volatility_signal", "BOOLEAN"),
        bigquery.SchemaField("UPTREND", "BOOLEAN"),
        bigquery.SchemaField("obv_yesterday", "FLOAT64"),
        bigquery.SchemaField("obv_filter", "BOOLEAN"),
        bigquery.SchemaField("GREEN4", "BOOLEAN"),
        bigquery.SchemaField("momentum_20", "FLOAT64"),
        bigquery.SchemaField("momentum_filter", "BOOLEAN"),
        bigquery.SchemaField("atr_ma", "FLOAT64"),
        bigquery.SchemaField("GREEN2", "BOOLEAN"),
        bigquery.SchemaField("atr_filter", "BOOLEAN"),
        bigquery.SchemaField("buy_signal", "BOOLEAN"),
        bigquery.SchemaField("buy_price", "FLOAT64"),
        bigquery.SchemaField("sell_price", "FLOAT64"),
        bigquery.SchemaField("returns", "FLOAT64"),
        bigquery.SchemaField("cumulative_returns", "FLOAT64"),
        bigquery.SchemaField("buy_hold_returns", "FLOAT64"),
        bigquery.SchemaField("entry_type", "STRING"),
        bigquery.SchemaField("daily_return", "FLOAT64"),
        bigquery.SchemaField("buy_hold_return", "FLOAT64"),
    ]
    return schema

def process_csv_file(filepath):
    """CSV 파일을 처리하여 DataFrame으로 변환"""
    # 파일명에서 ticker 추출
    filename = os.path.basename(filepath)
    ticker = filename.replace("adx_only_", "").replace(".csv", "")
    
    # CSV 읽기
    df = pd.read_csv(filepath)
    
    # ticker 컬럼 추가
    df['ticker'] = ticker
    
    # date 컬럼을 datetime으로 변환
    df['date'] = pd.to_datetime(df['date'])
    
    # 빈 문자열을 None으로 변환
    df = df.replace('', None)
    
    # Boolean 컬럼 처리
    bool_columns = ['volatility_signal', 'UPTREND', 'obv_filter', 'GREEN4', 
                    'momentum_filter', 'GREEN2', 'atr_filter', 'buy_signal']
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    
    return df

def main():
    """메인 실행 함수"""
    # BigQuery 클라이언트 생성
    client = get_bigquery_client()
    
    # 테이블 참조
    table_ref = client.dataset(DATASET_ID).table(TABLE_ID)
    
    # 테이블이 존재하는지 확인
    try:
        client.get_table(table_ref)
        print(f"테이블 {DATASET_ID}.{TABLE_ID}이 이미 존재합니다. 데이터를 추가합니다.")
    except:
        # 테이블이 없으면 생성
        print(f"테이블 {DATASET_ID}.{TABLE_ID}을 생성합니다.")
        schema = create_table_schema()
        table = bigquery.Table(table_ref, schema=schema)
        table = client.create_table(table)
        print(f"테이블 {table.project}.{table.dataset_id}.{table.table_id} 생성 완료")
    
    # CSV 파일들 찾기
    csv_files = glob.glob("Part4/adx_only*.csv")
    print(f"총 {len(csv_files)}개의 CSV 파일을 찾았습니다.")
    
    # 모든 데이터를 하나의 DataFrame으로 결합
    all_data = []
    
    for i, filepath in enumerate(csv_files):
        print(f"처리 중: {i+1}/{len(csv_files)} - {os.path.basename(filepath)}")
        df = process_csv_file(filepath)
        all_data.append(df)
    
    # 전체 데이터 결합
    print("데이터 결합 중...")
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"총 {len(combined_df)}개의 행을 업로드합니다.")
    
    # BigQuery에 업로드
    print("BigQuery에 업로드 중...")
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # 기존 데이터 덮어쓰기
        autodetect=False,
        schema=create_table_schema()
    )
    
    job = client.load_table_from_dataframe(
        combined_df,
        table_ref,
        job_config=job_config
    )
    
    job.result()  # 작업 완료 대기
    
    print(f"✅ 업로드 완료! 테이블: {DATASET_ID}.{TABLE_ID}")
    print(f"총 {job.output_rows}개의 행이 업로드되었습니다.")
    
    # 업로드 확인
    query = f"""
    SELECT ticker, COUNT(*) as row_count 
    FROM `{client.project}.{DATASET_ID}.{TABLE_ID}` 
    GROUP BY ticker 
    ORDER BY ticker
    LIMIT 10
    """
    
    print("\n업로드된 데이터 샘플:")
    for row in client.query(query):
        print(f"  {row.ticker}: {row.row_count} rows")

if __name__ == "__main__":
    main()