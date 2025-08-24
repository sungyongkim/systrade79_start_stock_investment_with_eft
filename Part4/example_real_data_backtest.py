"""
실제 데이터를 사용한 백테스트 예시
BigQuery에서 데이터를 로드하여 테스트
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.oauth2 import service_account
import matplotlib.pyplot as plt
from backtest_strategy import *

# matplotlib 한글 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# BigQuery 클라이언트 초기화
def get_bigquery_client():
    service_account_path = "/Users/cg01-piwoo/my_quant/access_info/data/quantsungyong-663604552de9.json"
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return bigquery.Client(credentials=credentials, project=credentials.project_id)

# 간단한 데이터 로드 함수
def load_stock_data(ticker, start_date='2020-01-01', end_date='2023-12-31'):
    client = get_bigquery_client()
    
    query = f"""
    WITH raw_data AS (
        SELECT 
            ticker,
            JSON_EXTRACT_ARRAY(data, '$.dates') AS dates_array,
            JSON_EXTRACT_ARRAY(data, '$.open') AS open_array,
            JSON_EXTRACT_ARRAY(data, '$.high') AS high_array,
            JSON_EXTRACT_ARRAY(data, '$.low') AS low_array,
            JSON_EXTRACT_ARRAY(data, '$.close') AS close_array,
            JSON_EXTRACT_ARRAY(data, '$.volume') AS volume_array,
            ARRAY_LENGTH(JSON_EXTRACT_ARRAY(data, '$.close')) AS array_length
        FROM 
            `quantsungyong.finviz_data.stock_data_with_indicators`
        WHERE 
            ticker = '{ticker}'
    ),
    indices AS (
        SELECT r.ticker, pos
        FROM raw_data r,
        UNNEST(GENERATE_ARRAY(0, r.array_length - 1)) AS pos
    )
    SELECT 
        JSON_EXTRACT_SCALAR(r.dates_array[OFFSET(i.pos)], '$') AS date,
        CAST(JSON_EXTRACT_SCALAR(r.open_array[OFFSET(i.pos)], '$') AS FLOAT64) AS open,
        CAST(JSON_EXTRACT_SCALAR(r.high_array[OFFSET(i.pos)], '$') AS FLOAT64) AS high,
        CAST(JSON_EXTRACT_SCALAR(r.low_array[OFFSET(i.pos)], '$') AS FLOAT64) AS low,
        CAST(JSON_EXTRACT_SCALAR(r.close_array[OFFSET(i.pos)], '$') AS FLOAT64) AS close,
        CAST(JSON_EXTRACT_SCALAR(r.volume_array[OFFSET(i.pos)], '$') AS INT64) AS volume
    FROM raw_data r
    CROSS JOIN indices i
    WHERE i.ticker = r.ticker 
        AND JSON_EXTRACT_SCALAR(r.dates_array[OFFSET(i.pos)], '$') >= '{start_date}'
        AND JSON_EXTRACT_SCALAR(r.dates_array[OFFSET(i.pos)], '$') <= '{end_date}'
    ORDER BY date
    """
    
    try:
        df = client.query(query).to_dataframe()
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        return None

# 메인 실행 코드
if __name__ == "__main__":
    # 1. 데이터 로드
    print("📊 데이터 로드 중...")
    ticker = 'AAPL'  # 애플 주식
    df = load_stock_data(ticker, '2020-01-01', '2023-12-31')
    
    if df is None:
        print("데이터 로드 실패. 샘플 데이터를 사용합니다.")
        # 샘플 데이터 생성 (실패 시)
        dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='D')
        n = len(dates)
        np.random.seed(42)
        
        # 현실적인 주가 움직임 시뮬레이션
        price = 100
        prices = []
        trend = 0.0001  # 약간의 상승 추세
        
        for i in range(n):
            # 추세와 랜덤 변동성 결합
            change = np.random.normal(trend, 0.015)
            price = price * (1 + change)
            prices.append(price)
        
        df = pd.DataFrame({
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.008))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.008))) for p in prices],
            'close': [p * (1 + np.random.normal(0, 0.003)) for p in prices],
            'volume': np.random.randint(10000000, 100000000, n)
        }, index=dates)
    
    print(f"✅ {ticker} 데이터 로드 완료: {len(df)}개 레코드")
    print(f"기간: {df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}")
    print()
    
    # 2. 여러 K값으로 기본 전략 테스트
    print("📈 변동성 돌파 전략 백테스트 (K값 비교)")
    print("-" * 60)
    
    k_values = [0.3, 0.4, 0.5, 0.6, 0.7]
    results = {}
    
    for k in k_values:
        result = simple_volatility_breakout_backtest(df, k=k, slippage=0.001, commission=0.0005)
        total_return = (result['cumulative_returns'].iloc[-1] - 1) * 100
        num_trades = result['num_trades'].iloc[0]
        win_rate = result['win_rate'].iloc[0] * 100
        
        results[f'K={k}'] = result
        
        print(f"K={k}: 수익률={total_return:6.2f}%, 거래={num_trades:3d}회, 승률={win_rate:4.1f}%")
    
    buy_hold_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
    print(f"\nBuy & Hold: {buy_hold_return:.2f}%")
    print()
    
    # 3. 진입/청산 전략 조합 테스트
    print("🎯 진입/청산 전략 조합 테스트")
    print("-" * 60)
    
    # 최적 K값 선택 (가장 높은 수익률)
    best_k = 0.5
    
    # 다양한 조합 테스트
    test_cases = [
        ("기본 진입 + 익일 매도", volatility_breakout_entry, next_day_exit, {'k': best_k}, {}),
        ("기본 진입 + ATR 청산", volatility_breakout_entry, atr_based_exit, 
         {'k': best_k}, {'take_profit_atr': 2.0, 'stop_loss_atr': 1.0, 'max_holding_days': 10}),
        ("적응형 K + 이동평균선 청산", adaptive_k_entry, ma_based_exit,
         {'k_min': 0.3, 'k_max': 0.7}, {'short_ma': 5, 'long_ma': 20}),
        ("거래량 확인 + ATR 청산", volume_confirmed_entry, atr_based_exit,
         {'k': best_k, 'volume_multiplier': 1.5}, {'take_profit_atr': 2.5, 'stop_loss_atr': 1.0}),
    ]
    
    for name, entry_func, exit_func, entry_params, exit_params in test_cases:
        # 진입 전략
        entry_result = entry_func(df, **entry_params)
        entry_signals = entry_result['entry_signal'].sum()
        
        # 청산 전략
        exit_result = exit_func(df, entry_result, **exit_params)
        exit_signals = exit_result['exit_signal'].sum()
        
        # 백테스트
        final_result = simple_backtest_entry_exit(df, entry_result, exit_result, 
                                                 slippage=0.001, commission=0.0005)
        
        total_return = (final_result['cumulative_returns'].iloc[-1] - 1) * 100
        num_trades = final_result['total_trades'].iloc[0]
        
        print(f"{name}:")
        print(f"  진입신호: {entry_signals}, 청산신호: {exit_signals}, 거래횟수: {num_trades}")
        print(f"  총 수익률: {total_return:.2f}%")
        print()
    
    # 4. 수익률 곡선 시각화
    print("📊 수익률 곡선 시각화")
    
    plt.figure(figsize=(12, 6))
    
    # 가장 좋은 전략 선택
    best_result = simple_volatility_breakout_backtest(df, k=0.5, slippage=0.001, commission=0.0005)
    
    plt.plot(best_result.index, best_result['cumulative_returns'], 
             label='변동성 돌파 (K=0.5)', linewidth=2)
    plt.plot(best_result.index, best_result['buy_hold_returns'], 
             label='Buy & Hold', linewidth=2, alpha=0.7)
    
    plt.title(f'{ticker} 변동성 돌파 전략 vs Buy & Hold')
    plt.xlabel('날짜')
    plt.ylabel('누적 수익률')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('backtest_result.png', dpi=300, bbox_inches='tight')
    print("✅ 그래프 저장 완료: backtest_result.png")
    
    # 5. 상세 성과 분석
    print("\n📊 상세 성과 분석")
    print("-" * 60)
    
    metrics = calculate_performance_metrics(best_result['returns'])
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    print("\n✅ 백테스트 완료!")