"""
backtest_strategy 라이브러리 간단한 테스트
"""

import pandas as pd
import numpy as np
from datetime import datetime
from backtest_strategy import *

# 테스트용 샘플 데이터 생성
np.random.seed(42)
dates = pd.date_range(start='2020-01-01', end='2021-12-31', freq='D')
n = len(dates)

# 가격 데이터 시뮬레이션
price = 100
prices = []
for i in range(n):
    change = np.random.normal(0.001, 0.02)
    price = price * (1 + change)
    prices.append(price)

df = pd.DataFrame({
    'open': prices,
    'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
    'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
    'close': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
    'volume': np.random.randint(1000000, 10000000, n)
}, index=dates)

print(f"데이터 준비 완료: {len(df)}개 레코드\n")

# 1. 기본 전략 테스트: 변동성 돌파 + 익일 매도
print("1. 기본 전략 테스트 (변동성 돌파 + 익일 매도)")
result1 = volatility_breakout_next_day_exit(df, k=0.5, slippage=0.002, commission=0.001)
print(f"- 총 수익률: {(result1['cumulative_returns'].iloc[-1] - 1) * 100:.2f}%")
print(f"- 거래 횟수: {result1['entry_signal'].sum()}")  # num_trades 대신 entry_signal 사용
print()

# 2. 진입 전략 테스트
print("2. 진입 전략 개별 테스트")

# 기본 변동성 돌파
entry1 = volatility_breakout_entry(df, k=0.5)
print(f"- 기본 변동성 돌파: {entry1['entry_signal'].sum()}개 신호")

# 적응형 K값
entry2 = adaptive_k_entry(df, lookback=20, k_min=0.3, k_max=0.7)
print(f"- 적응형 K값: {entry2['entry_signal'].sum()}개 신호")

# 거래량 확인
entry3 = volume_confirmed_entry(df, k=0.5, volume_multiplier=1.5)
print(f"- 거래량 확인: {entry3['entry_signal'].sum()}개 신호")
print()

# 3. 진입 + 청산 조합 테스트
print("3. 진입 + 청산 전략 조합 테스트")

# 테스트 1: 기본 진입 + ATR 청산
print("\n테스트 1: 기본 변동성 돌파 + ATR 기반 청산")
entry_result = volatility_breakout_entry(df, k=0.5)
exit_result = atr_based_exit(df, entry_result, take_profit_atr=2.0, stop_loss_atr=1.0)

# exit_result 데이터 확인
print(f"- 진입 신호: {entry_result['entry_signal'].sum()}개")
print(f"- 청산 신호: {exit_result['exit_signal'].sum()}개")

# run_backtest로 최종 백테스트
final_result = run_backtest(
    df,
    volatility_breakout_entry,
    atr_based_exit,
    entry_params={'k': 0.5},
    exit_params={'take_profit_atr': 2.0, 'stop_loss_atr': 1.0},
    slippage=0.002,
    commission=0.001
)

print(f"- 총 수익률: {(final_result['cumulative_returns'].iloc[-1] - 1) * 100:.2f}%")
print(f"- Buy & Hold: {(final_result['buy_hold_returns'].iloc[-1] - 1) * 100:.2f}%")

# 테스트 2: 적응형 K + 이동평균선 청산
print("\n테스트 2: 적응형 K값 + 이동평균선 청산")
final_result2 = run_backtest(
    df,
    adaptive_k_entry,
    ma_based_exit,
    entry_params={'lookback': 20, 'k_min': 0.3, 'k_max': 0.7},
    exit_params={'short_ma': 5, 'long_ma': 20},
    slippage=0.002,
    commission=0.001
)

print(f"- 총 수익률: {(final_result2['cumulative_returns'].iloc[-1] - 1) * 100:.2f}%")

# 성과 지표 계산
metrics = calculate_performance_metrics(final_result['returns'])
print("\n📊 상세 성과 지표:")
for key, value in metrics.items():
    print(f"- {key}: {value}")

print("\n✅ 테스트 완료!")