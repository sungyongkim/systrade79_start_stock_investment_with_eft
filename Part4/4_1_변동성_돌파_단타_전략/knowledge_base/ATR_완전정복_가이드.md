# ATR(Average True Range) 완전정복 가이드

> 변동성을 측정하고 활용하는 가장 강력한 지표

## 목차
1. [ATR의 정의와 개념](#1-atr의-정의와-개념)
2. [ATR 계산 방법](#2-atr-계산-방법)
3. [ATR의 특징과 해석](#3-atr의-특징과-해석)
4. [ATR을 활용한 매매 전략](#4-atr을-활용한-매매-전략)
5. [변동성 돌파 전략에서의 ATR 활용](#5-변동성-돌파-전략에서의-atr-활용)
6. [실전 코드 예시](#6-실전-코드-예시)
7. [주의사항과 한계](#7-주의사항과-한계)

---

## 1. ATR의 정의와 개념

### 1.1 ATR이란?

**ATR (Average True Range)**는 J. Welles Wilder가 1978년 개발한 변동성 지표입니다.

- **목적**: 주가의 변동성(Volatility)을 측정
- **특징**: 가격의 방향이 아닌 움직임의 크기를 측정
- **장점**: 갭(Gap)을 포함한 실제 변동폭 반영

### 1.2 왜 ATR이 중요한가?

1. **리스크 관리**: 변동성에 따른 포지션 크기 조절
2. **진입/청산 시점**: 변동성 확대/축소 시기 포착
3. **손절매 설정**: 변동성 기반 동적 손절매
4. **필터링**: 변동성이 낮은 횡보장 회피

---

## 2. ATR 계산 방법

### 2.1 True Range (TR) 계산

True Range는 다음 세 값 중 최대값:

```
TR = MAX(
    고가 - 저가,                    # 당일 변동폭
    |고가 - 전일종가|,              # 상승 갭 포함
    |저가 - 전일종가|               # 하락 갭 포함
)
```

### 2.2 ATR 계산

```python
# 초기 ATR (첫 14일)
ATR = (TR1 + TR2 + ... + TR14) / 14

# 이후 ATR (지수이동평균)
ATR = (전일 ATR × 13 + 당일 TR) / 14
```

### 2.3 계산 예시

```
일자    고가    저가    종가    TR      ATR(14)
Day1    102     98      100     4.0     -
Day2    104     99      103     5.0     -
...
Day14   105     102     104     3.5     4.2
Day15   107     103     106     4.0     4.15
```

---

## 3. ATR의 특징과 해석

### 3.1 ATR 값의 의미

| ATR 상태 | 의미 | 시장 상황 |
|----------|------|-----------|
| ATR 상승 | 변동성 확대 | 추세 전환, 뉴스 영향, 불확실성 증가 |
| ATR 하락 | 변동성 축소 | 횡보장, 박스권, 추세 지속 |
| ATR 고점 | 극단적 변동성 | 패닉, 버블, 전환점 임박 |
| ATR 저점 | 극단적 안정 | 돌파 임박, 에너지 축적 |

### 3.2 ATR의 특성

1. **절대값**: 가격 수준에 따라 다름 (비교 시 주의)
2. **후행성**: 과거 데이터 기반 계산
3. **방향성 없음**: 상승/하락 구분 없이 변동폭만 측정
4. **민감도**: 기간 설정에 따라 변화 (14일이 표준)

---

## 4. ATR을 활용한 매매 전략

### 4.1 포지션 사이징 (Position Sizing)

```python
# ATR 기반 포지션 크기 결정
계좌_자산 = 1000000  # 100만원
리스크_비율 = 0.02  # 2%
최대_손실 = 계좌_자산 * 리스크_비율  # 2만원

# ATR의 2배를 손절 기준으로 설정
손절_거리 = ATR * 2
포지션_크기 = 최대_손실 / 손절_거리
```

### 4.2 동적 손절매 (Dynamic Stop Loss)

```python
# Chandelier Exit (샹들리에 이그짓)
매수가 = 100
최고가 = 105  # 보유 기간 중 최고가
손절가 = 최고가 - (ATR * 3)  # ATR의 3배 하락 시 손절

# 시간 경과에 따라 손절선 상향 조정
if 현재가 > 최고가:
    최고가 = 현재가
    손절가 = 최고가 - (ATR * 3)
```

### 4.3 변동성 돌파 진입

```python
# ATR 기반 돌파 확인
전일_ATR = ATR[전일]
돌파_기준 = 시가 + (전일_ATR * 0.5)

if 현재가 > 돌파_기준:
    매수_신호 = True
```

### 4.4 변동성 필터

```python
# 변동성이 확대될 때만 거래
ATR_20일_평균 = ATR.rolling(20).mean()

if ATR > ATR_20일_평균 * 1.2:  # ATR이 평균보다 20% 높을 때
    변동성_확대 = True
    거래_허용 = True
else:
    거래_허용 = False  # 횡보장 회피
```

---

## 5. 변동성 돌파 전략에서의 ATR 활용

### 5.1 기존 전략의 문제점

- 고정 K값 사용 (예: 0.3, 0.5)
- 모든 상황에 동일한 기준 적용
- 변동성 변화 미반영

### 5.2 ATR 기반 개선 방안

#### 1) 동적 K값 설정
```python
# 변동성에 따른 K값 조정
if ATR > ATR_평균 * 1.5:
    K = 0.7  # 높은 변동성: 보수적
elif ATR < ATR_평균 * 0.7:
    K = 0.3  # 낮은 변동성: 공격적
else:
    K = 0.5  # 보통
```

#### 2) ATR 필터 추가
```python
# ATR 상승 중일 때만 진입
ATR_상승 = ATR > ATR.shift(1)
ATR_평균초과 = ATR > ATR.rolling(20).mean()

if 변동성_돌파 and ATR_상승 and ATR_평균초과:
    매수_신호 = True
```

#### 3) ATR 기반 익절/손절
```python
# 진입 시점의 ATR 기록
진입_ATR = ATR[매수일]

# 목표가와 손절가 설정
목표가 = 매수가 + (진입_ATR * 2)    # 2 ATR 익절
손절가 = 매수가 - (진입_ATR * 1)    # 1 ATR 손절
```

### 5.3 통합 전략 예시

```python
def volatility_breakout_with_atr(df, base_k=0.5, atr_period=14):
    """ATR을 활용한 변동성 돌파 전략"""
    
    # ATR 계산
    df['TR'] = df[['high', 'low', 'close']].apply(
        lambda x: max(
            x['high'] - x['low'],
            abs(x['high'] - df['close'].shift(1)),
            abs(x['low'] - df['close'].shift(1))
        ), axis=1
    )
    df['ATR'] = df['TR'].rolling(atr_period).mean()
    
    # ATR 기반 동적 K값
    atr_mean = df['ATR'].rolling(20).mean()
    df['dynamic_k'] = df.apply(
        lambda x: 0.7 if x['ATR'] > atr_mean * 1.5 
        else 0.3 if x['ATR'] < atr_mean * 0.7 
        else base_k, axis=1
    )
    
    # 변동성 필터
    df['atr_rising'] = df['ATR'] > df['ATR'].shift(1)
    df['high_volatility'] = df['ATR'] > atr_mean
    
    # 매수 신호
    df['target'] = df['open'] + df['range'].shift(1) * df['dynamic_k']
    df['buy_signal'] = (
        (df['high'] > df['target']) &  # 변동성 돌파
        df['atr_rising'] &              # ATR 상승 중
        df['high_volatility']           # 높은 변동성
    )
    
    return df
```

---

## 6. 실전 코드 예시

### 6.1 ATR 계산 함수

```python
import pandas as pd
import numpy as np

def calculate_atr(df, period=14):
    """
    ATR 계산 함수
    
    Parameters:
    - df: DataFrame with 'high', 'low', 'close' columns
    - period: ATR 계산 기간 (기본 14)
    
    Returns:
    - Series: ATR values
    """
    # True Range 계산
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift(1))
    low_close = np.abs(df['low'] - df['close'].shift(1))
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # ATR 계산 (지수이동평균)
    atr = tr.rolling(window=period).mean()
    
    # 더 정확한 EMA 방식
    # atr = tr.ewm(span=period, adjust=False).mean()
    
    return atr
```

### 6.2 ATR 기반 거래 신호

```python
def generate_atr_signals(df, atr_period=14, atr_multiplier=2):
    """
    ATR 기반 거래 신호 생성
    
    Parameters:
    - df: 주가 데이터
    - atr_period: ATR 계산 기간
    - atr_multiplier: ATR 배수
    
    Returns:
    - DataFrame with signals
    """
    # ATR 계산
    df['ATR'] = calculate_atr(df, atr_period)
    
    # ATR 밴드
    df['upper_band'] = df['close'] + df['ATR'] * atr_multiplier
    df['lower_band'] = df['close'] - df['ATR'] * atr_multiplier
    
    # 시그널 생성
    df['long_signal'] = df['close'] > df['upper_band'].shift(1)
    df['short_signal'] = df['close'] < df['lower_band'].shift(1)
    
    # 포지션 크기 (리스크 2%)
    account_value = 1000000  # 100만원
    risk_per_trade = 0.02
    df['position_size'] = (account_value * risk_per_trade) / (df['ATR'] * 2)
    
    return df
```

### 6.3 백테스팅 예시

```python
def backtest_atr_strategy(df, initial_capital=1000000):
    """
    ATR 전략 백테스팅
    """
    capital = initial_capital
    position = 0
    trades = []
    
    for i in range(1, len(df)):
        current = df.iloc[i]
        prev = df.iloc[i-1]
        
        # 진입
        if current['long_signal'] and position == 0:
            position = current['position_size']
            entry_price = current['close']
            stop_loss = entry_price - (current['ATR'] * 2)
            take_profit = entry_price + (current['ATR'] * 3)
            
            trades.append({
                'date': current.name,
                'action': 'BUY',
                'price': entry_price,
                'size': position,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            })
        
        # 청산
        elif position > 0:
            if (current['low'] <= stop_loss or 
                current['high'] >= take_profit or
                current['short_signal']):
                
                exit_price = min(max(current['open'], stop_loss), take_profit)
                pnl = (exit_price - entry_price) * position
                capital += pnl
                
                trades.append({
                    'date': current.name,
                    'action': 'SELL',
                    'price': exit_price,
                    'pnl': pnl,
                    'capital': capital
                })
                
                position = 0
    
    return pd.DataFrame(trades), capital
```

---

## 7. 주의사항과 한계

### 7.1 ATR의 한계

1. **후행 지표**: 과거 데이터 기반으로 미래 예측 불가
2. **방향성 부재**: 상승/하락 방향 예측 불가
3. **절대값 문제**: 종목 간 직접 비교 어려움
4. **갭 처리**: 극단적 갭은 ATR을 왜곡할 수 있음

### 7.2 사용 시 주의사항

1. **다른 지표와 병행**: ATR 단독 사용 지양
2. **시장 상황 고려**: 뉴스, 이벤트 시 ATR 급변
3. **종목 특성 반영**: 업종별, 시가총액별 차이
4. **백테스팅 필수**: 실전 적용 전 충분한 검증

### 7.3 개선 방안

```python
# 1. 정규화된 ATR (NATR)
NATR = (ATR / Close) * 100  # 백분율로 표현

# 2. 적응형 ATR
if 추세장:
    ATR_period = 10  # 빠른 반응
else:
    ATR_period = 20  # 느린 반응

# 3. 다중 시간대 ATR
ATR_short = calculate_atr(df, 7)
ATR_medium = calculate_atr(df, 14)
ATR_long = calculate_atr(df, 28)

# 모두 상승 중일 때만 진입
if ATR_short > ATR_medium > ATR_long:
    강한_변동성_확대 = True
```

---

## 결론

ATR은 변동성을 측정하는 가장 신뢰할 수 있는 지표 중 하나입니다. 

**핵심 활용법:**
1. **리스크 관리**: 포지션 크기와 손절매 설정
2. **필터링**: 변동성 환경에 따른 전략 적용
3. **최적화**: 동적 파라미터 조정

**변동성 돌파 전략에서의 활용:**
- ATR 상승 시에만 진입 → 거래 빈도 감소
- ATR 기반 K값 조정 → 시장 적응력 향상
- ATR 배수로 목표가 설정 → 합리적 기대수익

ATR을 마스터하면 시장의 숨결을 읽고, 더 나은 타이밍에 더 적절한 크기로 거래할 수 있습니다.