"""
간단한 백테스트 테스트
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

# 1. 간단한 변동성 돌파 백테스트
print("1. 간단한 변동성 돌파 백테스트")
result = simple_volatility_breakout_backtest(df, k=0.5, slippage=0.002, commission=0.001)

print(f"- 총 수익률: {(result['cumulative_returns'].iloc[-1] - 1) * 100:.2f}%")
print(f"- Buy & Hold: {(result['buy_hold_returns'].iloc[-1] - 1) * 100:.2f}%")
print(f"- 거래 횟수: {result['num_trades'].iloc[0]}")
print(f"- 승률: {result['win_rate'].iloc[0] * 100:.1f}%")
print()

# 2. 진입/청산 전략 조합 테스트
print("2. 진입/청산 전략 조합 테스트")

# 진입 전략: 기본 변동성 돌파
entry_result = volatility_breakout_entry(df, k=0.5)
print(f"- 진입 신호: {entry_result['entry_signal'].sum()}개")

# 청산 전략: 익일 매도
exit_result = next_day_exit(df, entry_result)
print(f"- 청산 신호: {exit_result['exit_signal'].sum()}개")

# 간단한 백테스트
final_result = simple_backtest_entry_exit(df, entry_result, exit_result, slippage=0.002, commission=0.001)
print(f"- 총 수익률: {(final_result['cumulative_returns'].iloc[-1] - 1) * 100:.2f}%")
print(f"- 거래 횟수: {final_result['total_trades'].iloc[0]}")
print()

# 3. ATR 기반 청산 전략 테스트
print("3. ATR 기반 청산 전략 테스트")

# 청산 전략: ATR 기반
exit_result2 = atr_based_exit(df, entry_result, take_profit_atr=2.0, stop_loss_atr=1.0, max_holding_days=10)
print(f"- 청산 신호: {exit_result2['exit_signal'].sum()}개")

# 평균 보유일수 계산
exits_with_holding = exit_result2[exit_result2['exit_signal'] == True]
if len(exits_with_holding) > 0:
    avg_holding = exits_with_holding['holding_days'].mean()
    print(f"- 평균 보유일수: {avg_holding:.1f}일")
    
    # 청산 사유 분석
    if 'exit_reason' in exit_result2.columns:
        exit_reasons = exits_with_holding['exit_reason'].value_counts()
        print("\n청산 사유 분석:")
        for reason, count in exit_reasons.items():
            print(f"  - {reason}: {count}회 ({count/len(exits_with_holding)*100:.1f}%)")

# 백테스트
final_result2 = simple_backtest_entry_exit(df, entry_result, exit_result2, slippage=0.002, commission=0.001)
print(f"\n- 총 수익률: {(final_result2['cumulative_returns'].iloc[-1] - 1) * 100:.2f}%")
print(f"- 거래 횟수: {final_result2['total_trades'].iloc[0]}")

print("\n✅ 테스트 완료!")