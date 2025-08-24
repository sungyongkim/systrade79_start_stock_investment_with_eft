"""
경고 메시지 없이 백테스트 실행
"""

import pandas as pd
import numpy as np
import warnings

# FutureWarning 무시
warnings.filterwarnings('ignore', category=FutureWarning)

from backtest_strategy import *

# 테스트 데이터 생성
np.random.seed(42)
dates = pd.date_range(start='2020-01-01', end='2021-12-31', freq='D')
n = len(dates)

# 현실적인 주가 데이터 시뮬레이션
price = 100
prices = []
trend = 0.0002  # 약간의 상승 추세

for i in range(n):
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

print("📊 백테스트 실행 (경고 메시지 제거)")
print("=" * 60)

# 1. 간단한 변동성 돌파
result1 = simple_volatility_breakout_backtest(df, k=0.5)
print(f"변동성 돌파 (K=0.5): {(result1['cumulative_returns'].iloc[-1] - 1) * 100:.2f}%")

# 2. 진입/청산 조합
entry = volatility_breakout_entry(df, k=0.5)
exit = atr_based_exit(df, entry, take_profit_atr=2.0, stop_loss_atr=1.0)
result2 = simple_backtest_entry_exit(df, entry, exit)
print(f"ATR 청산 전략: {(result2['cumulative_returns'].iloc[-1] - 1) * 100:.2f}%")

# 3. 전체 백테스트
result3 = run_backtest(
    df,
    volatility_breakout_entry,
    atr_based_exit,
    entry_params={'k': 0.5},
    exit_params={'take_profit_atr': 2.0, 'stop_loss_atr': 1.0},
    slippage=0.002,
    commission=0.001
)
print(f"전체 백테스트: {(result3['cumulative_returns'].iloc[-1] - 1) * 100:.2f}%")

print("\n✅ 경고 메시지 없이 완료!")