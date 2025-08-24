"""
개선된 전략 비교 테스트
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from backtest_strategy import *

# 테스트 데이터 생성
np.random.seed(42)
dates = pd.date_range(start='2020-01-01', end='2021-12-31', freq='D')
n = len(dates)

# 현실적인 주가 데이터
price = 100
prices = []
trend = 0.0003  # 연 7% 정도 상승

for i in range(n):
    change = np.random.normal(trend, 0.012)
    price = price * (1 + change)
    prices.append(price)

df = pd.DataFrame({
    'open': prices,
    'high': [p * (1 + abs(np.random.normal(0, 0.006))) for p in prices],
    'low': [p * (1 - abs(np.random.normal(0, 0.006))) for p in prices],
    'close': [p * (1 + np.random.normal(0, 0.002)) for p in prices],
    'volume': np.random.randint(10000000, 100000000, n)
}, index=dates)

print("📊 개선된 전략 비교 테스트")
print("=" * 80)

# 1. 모든 진입 전략 비교
print("\n1. 진입 전략 비교 (익일 매도 기준)")
print("-" * 60)
entry_comparison = compare_all_entry_strategies(df, k_values=[0.3, 0.5, 0.7])
print(entry_comparison)

# 2. 모든 청산 전략 비교
print("\n2. 청산 전략 비교 (변동성 돌파 K=0.5 기준)")
print("-" * 60)
exit_comparison = compare_all_exit_strategies(df, entry_k=0.5)
print(exit_comparison)

# 3. 최적 조합 찾기
print("\n3. 최적 진입/청산 조합 TOP 3")
print("-" * 60)
best_combinations = find_best_combination(df, top_n=3)
print(best_combinations)

print("\n✅ 테스트 완료!")