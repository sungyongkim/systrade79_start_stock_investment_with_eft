# backtest_strategy

변동성 돌파 전략을 위한 백테스트 라이브러리

## 개요

이 라이브러리는 변동성 돌파 전략의 다양한 변형을 쉽게 백테스트할 수 있도록 설계되었습니다. 10가지 진입 전략과 11가지 청산 전략을 자유롭게 조합하여 사용할 수 있습니다.

## 설치

```bash
# 현재 디렉토리에서 직접 사용
from backtest_strategy import *
```

## 주요 기능

### 1. 진입 전략 (Entry Strategies)

- **volatility_breakout_entry**: 기본 변동성 돌파
- **adaptive_k_entry**: 시장 상황에 따라 K값 동적 조정
- **double_breakout_entry**: 이중 돌파 확인
- **volume_confirmed_entry**: 거래량 급증 확인
- **momentum_filtered_entry**: 상승 모멘텀 필터
- **gap_adjusted_entry**: 갭 상승/하락 조정
- **pattern_based_entry**: 캔들 패턴 인식
- **multi_timeframe_entry**: 멀티 타임프레임 확인
- **atr_filtered_entry**: ATR 기반 변동성 필터
- **composite_entry**: 복합 점수 기반

### 2. 청산 전략 (Exit Strategies)

- **next_day_exit**: 익일 시가 매도 (기본)
- **atr_based_exit**: ATR 기반 동적 익절/손절
- **ma_based_exit**: 이동평균선 기반
- **momentum_score_exit**: 모멘텀 점수 기반
- **volatility_based_exit**: 변동성 확대/축소 기반
- **partial_profit_exit**: 단계별 부분 익절
- **time_weighted_exit**: 시간 가중 청산
- **bollinger_exit**: 볼린저 밴드 기반
- **adx_trend_exit**: ADX 추세 강도 기반
- **pattern_based_exit**: 패턴 인식 기반
- **composite_score_exit**: 복합 점수 기반

### 3. 백테스트 함수

- **simple_volatility_breakout_backtest**: 간단한 변동성 돌파 백테스트
- **simple_backtest_entry_exit**: 진입/청산 결과로 백테스트
- **run_backtest**: 전체 백테스트 (자금관리 포함)
- **volatility_breakout_next_day_exit**: 변동성 돌파 + 익일 매도

### 4. 분석 도구

- **calculate_performance_metrics**: 성과 지표 계산
- **plot_strategy_comparison**: 전략 비교 시각화
- **analyze_exit_reasons**: 청산 사유 분석

## 빠른 시작

### 기본 사용법

```python
import pandas as pd
from backtest_strategy import *

# 데이터 준비 (OHLCV 필수)
df = pd.read_csv('stock_data.csv', index_col='date', parse_dates=True)

# 1. 간단한 변동성 돌파 백테스트
result = simple_volatility_breakout_backtest(df, k=0.5, slippage=0.002, commission=0.001)
print(f"총 수익률: {(result['cumulative_returns'].iloc[-1] - 1) * 100:.2f}%")
```

### 진입/청산 전략 조합

```python
# 진입 전략: 적응형 K값
entry_result = adaptive_k_entry(df, lookback=20, k_min=0.3, k_max=0.7)

# 청산 전략: ATR 기반
exit_result = atr_based_exit(df, entry_result, 
                            take_profit_atr=2.0, 
                            stop_loss_atr=1.0,
                            max_holding_days=20)

# 백테스트 실행
final_result = simple_backtest_entry_exit(df, entry_result, exit_result)
```

### 여러 전략 비교

```python
# 개선된 비교 함수 사용
# 진입 전략 비교 (DataFrame 반환)
entry_df = compare_all_entry_strategies(df, k_values=[0.3, 0.5, 0.7])
print(entry_df)

# 청산 전략 비교 (DataFrame 반환)
exit_df = compare_all_exit_strategies(df, entry_k=0.5)
print(exit_df)

# 최적 조합 찾기
best_combinations = find_best_combination(df, top_n=3)
print(best_combinations)

# 시각화
strategies = {
    '기본': result1,
    'ATR': result2,
    'MA': result3
}
plot_strategy_comparison(strategies)
```

## 데이터 형식

입력 데이터는 다음 컬럼을 포함해야 합니다:
- `open`: 시가
- `high`: 고가
- `low`: 저가
- `close`: 종가
- `volume`: 거래량 (선택사항)

인덱스는 날짜(datetime) 형식이어야 합니다.

## 성과 지표

`calculate_performance_metrics` 함수는 다음 지표를 계산합니다:
- 누적 수익률
- 연환산 수익률
- 샤프 비율
- 최대 낙폭 (MDD)
- 승률
- 평균 손익
- 손익비
- Calmar 비율
- 거래 횟수

## 예제 코드

### 예제 1: 변동성 돌파 + 익일 매도

```python
# 기본 전략
result = volatility_breakout_next_day_exit(df, k=0.5)

# 성과 분석
metrics = calculate_performance_metrics(result['returns'])
for key, value in metrics.items():
    print(f"{key}: {value}")
```

### 예제 2: 거래량 확인 + ATR 청산

```python
# 진입: 거래량 확인
entry = volume_confirmed_entry(df, k=0.5, volume_multiplier=1.5)

# 청산: ATR 기반
exit = atr_based_exit(df, entry, take_profit_atr=2.5, stop_loss_atr=1.0)

# 백테스트
result = simple_backtest_entry_exit(df, entry, exit)
```

### 예제 3: 최적 K값 찾기

```python
k_values = [0.3, 0.4, 0.5, 0.6, 0.7]
results = {}

for k in k_values:
    result = simple_volatility_breakout_backtest(df, k=k)
    total_return = (result['cumulative_returns'].iloc[-1] - 1) * 100
    results[k] = total_return
    print(f"K={k}: {total_return:.2f}%")
```

## 주의사항

1. **데이터 품질**: 정확한 OHLCV 데이터 필요
2. **거래 비용**: 슬리피지와 수수료를 현실적으로 설정
3. **과적합 방지**: 과도한 파라미터 최적화 주의
4. **검증**: 백테스트 결과를 실전 적용 전 충분히 검증

## 경고 메시지 해결

pandas FutureWarning이 발생하는 경우:
```python
import pandas as pd
# 미래 동작 옵션 설정
pd.set_option('future.no_silent_downcasting', True)
```

## 파일 구조

```
backtest_strategy/
├── __init__.py              # 패키지 초기화
├── base_strategies.py       # 기본 전략
├── entry_strategies.py      # 진입 전략들
├── exit_strategies.py       # 청산 전략들
├── combined_strategies.py   # 통합 백테스트
├── simple_backtest.py       # 간단한 백테스트
├── utils.py                 # 유틸리티 함수
└── README.md               # 이 문서
```

## 라이선스

이 프로젝트는 개인 학습 및 연구 목적으로 제작되었습니다.

## 기여

버그 리포트나 기능 제안은 이슈를 통해 제출해주세요.