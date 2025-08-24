"""
다양한 진입(Entry) 전략 구현
변동성 돌파를 기반으로 한 여러 진입 조건들
"""

import pandas as pd
import numpy as np
from .base_strategies import calculate_atr


def volatility_breakout_entry(df, k=0.5):
    """
    기본 변동성 돌파 진입 전략
    
    Parameters:
    - df: 주가 데이터프레임
    - k: K값 (기본 0.5)
    
    Returns:
    - DataFrame: 진입 신호가 추가된 결과
    """
    result = df.copy()
    
    # 전일 Range 계산
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    
    # 진입가 계산 (당일 시가 + 전일 Range × K)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    
    # 변동성 돌파 신호
    result['entry_signal'] = result['high'] > result['target_price']
    result['entry_price'] = result['target_price']
    
    return result


def adaptive_k_entry(df, lookback=20, k_min=0.3, k_max=0.7):
    """
    적응형 K값 진입 전략
    시장 상황에 따라 K값을 동적으로 조정
    
    Parameters:
    - lookback: K값 최적화를 위한 과거 기간
    - k_min: 최소 K값
    - k_max: 최대 K값
    """
    result = df.copy()
    
    # 전일 Range
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    
    # 적응형 K값 계산
    result['adaptive_k'] = k_min  # 기본값
    
    for i in range(lookback, len(result)):
        # 과거 lookback 기간 동안의 최적 K값 계산
        past_data = result.iloc[i-lookback:i]
        
        # 간단한 최적화: 변동성이 클수록 낮은 K값
        volatility = past_data['prev_range'].mean()
        avg_range = past_data['prev_range'].mean()
        
        if volatility > avg_range * 1.2:  # 높은 변동성
            optimal_k = k_min
        elif volatility < avg_range * 0.8:  # 낮은 변동성
            optimal_k = k_max
        else:
            # 선형 보간
            optimal_k = k_min + (k_max - k_min) * (1 - volatility / avg_range)
        
        result.iloc[i, result.columns.get_loc('adaptive_k')] = optimal_k
    
    # 진입가 계산
    result['target_price'] = result['open'] + (result['prev_range'] * result['adaptive_k'])
    result['entry_signal'] = result['high'] > result['target_price']
    result['entry_price'] = result['target_price']
    
    return result


def double_breakout_entry(df, k1=0.5, k2=0.7, holding_period=5):
    """
    이중 돌파 진입 전략
    1차 돌파 후 일정 기간 내 2차 돌파 시 진입
    """
    result = df.copy()
    
    # 전일 Range
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    
    # 1차, 2차 돌파선
    result['target_price_1'] = result['open'] + (result['prev_range'] * k1)
    result['target_price_2'] = result['open'] + (result['prev_range'] * k2)
    
    # 돌파 신호
    result['breakout_1'] = result['high'] > result['target_price_1']
    result['breakout_2'] = result['high'] > result['target_price_2']
    
    # 진입 신호 (1차 돌파 후 holding_period 내 2차 돌파)
    result['entry_signal'] = False
    result['entry_price'] = np.nan
    
    for i in range(holding_period, len(result)):
        # 과거 holding_period 동안 1차 돌파가 있었는지 확인
        recent_breakout_1 = result.iloc[i-holding_period:i]['breakout_1'].any()
        
        if recent_breakout_1 and result.iloc[i]['breakout_2']:
            result.iloc[i, result.columns.get_loc('entry_signal')] = True
            result.iloc[i, result.columns.get_loc('entry_price')] = result.iloc[i]['target_price_2']
    
    return result


def volume_confirmed_entry(df, k=0.5, volume_multiplier=1.5, volume_ma=20):
    """
    거래량 확인 진입 전략
    변동성 돌파 + 거래량 급증 확인
    """
    result = df.copy()
    
    # 기본 변동성 돌파
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    result['volatility_breakout'] = result['high'] > result['target_price']
    
    # 거래량 조건
    if 'volume' in df.columns:
        result['volume_ma'] = result['volume'].rolling(window=volume_ma).mean()
        result['volume_surge'] = result['volume'] > (result['volume_ma'] * volume_multiplier)
    else:
        result['volume_surge'] = True  # 거래량 데이터 없으면 항상 True
    
    # 최종 진입 신호
    result['entry_signal'] = result['volatility_breakout'] & result['volume_surge']
    result['entry_price'] = result['target_price']
    
    return result


def momentum_filtered_entry(df, k=0.5, momentum_period=20, momentum_threshold=0.05):
    """
    모멘텀 필터 진입 전략
    상승 모멘텀이 있을 때만 진입
    """
    result = df.copy()
    
    # 기본 변동성 돌파
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    result['volatility_breakout'] = result['high'] > result['target_price']
    
    # 모멘텀 계산
    result['momentum'] = result['close'].pct_change(periods=momentum_period)
    result['momentum_positive'] = result['momentum'] > momentum_threshold
    
    # RSI 추가 (옵션)
    delta = result['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    result['rsi'] = 100 - (100 / (1 + rs))
    result['rsi_bullish'] = (result['rsi'] > 30) & (result['rsi'] < 70)
    
    # 최종 진입 신호
    result['entry_signal'] = result['volatility_breakout'] & result['momentum_positive'] & result['rsi_bullish']
    result['entry_price'] = result['target_price']
    
    return result


def gap_adjusted_entry(df, k=0.5, gap_threshold=0.02):
    """
    갭 조정 진입 전략
    갭 상승/하락에 따라 진입가 조정
    """
    result = df.copy()
    
    # 전일 Range와 갭 계산
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    result['gap'] = (result['open'] - result['close'].shift(1)) / result['close'].shift(1)
    
    # 갭 종류 분류
    result['gap_up'] = result['gap'] > gap_threshold
    result['gap_down'] = result['gap'] < -gap_threshold
    result['gap_neutral'] = (~result['gap_up']) & (~result['gap_down'])
    
    # 갭에 따른 조정된 K값
    result['adjusted_k'] = k
    result.loc[result['gap_up'], 'adjusted_k'] = k * 0.8  # 갭상승시 K값 낮춤
    result.loc[result['gap_down'], 'adjusted_k'] = k * 1.2  # 갭하락시 K값 높임
    
    # 진입가 계산
    result['target_price'] = result['open'] + (result['prev_range'] * result['adjusted_k'])
    result['entry_signal'] = result['high'] > result['target_price']
    result['entry_price'] = result['target_price']
    
    return result


def pattern_based_entry(df, k=0.5, pattern_lookback=3):
    """
    패턴 기반 진입 전략
    특정 캔들 패턴 확인 후 변동성 돌파
    """
    result = df.copy()
    
    # 기본 변동성 돌파
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    result['volatility_breakout'] = result['high'] > result['target_price']
    
    # 패턴 인식
    result['is_bullish'] = result['close'] > result['open']
    result['body_size'] = abs(result['close'] - result['open']) / result['open']
    result['upper_shadow'] = (result['high'] - np.maximum(result['open'], result['close'])) / result['open']
    result['lower_shadow'] = (np.minimum(result['open'], result['close']) - result['low']) / result['open']
    
    # 패턴 1: 연속 양봉
    result['consecutive_bullish'] = False
    for i in range(pattern_lookback, len(result)):
        if all(result.iloc[i-j]['is_bullish'] for j in range(pattern_lookback)):
            result.iloc[i, result.columns.get_loc('consecutive_bullish')] = True
    
    # 패턴 2: 망치형 (Hammer)
    result['hammer'] = (
        (result['lower_shadow'] > result['body_size'] * 2) &
        (result['upper_shadow'] < result['body_size'] * 0.5) &
        (result['close'].pct_change() < -0.02)  # 하락 후 출현
    )
    
    # 패턴 3: 상승 돌파형
    result['breakout_pattern'] = (
        (result['close'] > result['high'].shift(1)) &
        (result['volume'] > result['volume'].rolling(20).mean() * 1.2) if 'volume' in df.columns else False
    )
    
    # 최종 진입 신호
    result['entry_signal'] = (
        result['volatility_breakout'] & 
        (result['consecutive_bullish'] | result['hammer'] | result['breakout_pattern'])
    )
    result['entry_price'] = result['target_price']
    
    return result


def multi_timeframe_entry(df, k=0.5, confirm_periods=[5, 20]):
    """
    멀티 타임프레임 진입 전략
    여러 기간의 추세 확인 후 진입
    """
    result = df.copy()
    
    # 기본 변동성 돌파
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    result['volatility_breakout'] = result['high'] > result['target_price']
    
    # 멀티 타임프레임 추세 확인
    result['trend_aligned'] = True
    
    for period in confirm_periods:
        # 각 기간별 이동평균
        result[f'ma_{period}'] = result['close'].rolling(window=period).mean()
        
        # 가격이 이동평균 위에 있는지
        result[f'above_ma_{period}'] = result['close'] > result[f'ma_{period}']
        
        # 이동평균이 상승 중인지
        result[f'ma_{period}_rising'] = result[f'ma_{period}'] > result[f'ma_{period}'].shift(1)
        
        # 추세 정렬 확인
        result['trend_aligned'] = result['trend_aligned'] & result[f'above_ma_{period}'] & result[f'ma_{period}_rising']
    
    # 최종 진입 신호
    result['entry_signal'] = result['volatility_breakout'] & result['trend_aligned']
    result['entry_price'] = result['target_price']
    
    return result


def atr_filtered_entry(df, k=0.5, atr_period=14, min_atr_percentile=30):
    """
    ATR 필터 진입 전략
    충분한 변동성이 있을 때만 진입
    """
    result = df.copy()
    
    # 기본 변동성 돌파
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    result['volatility_breakout'] = result['high'] > result['target_price']
    
    # ATR 계산
    result['atr'] = calculate_atr(df, period=atr_period)
    
    # ATR 백분위수 계산
    result['atr_percentile'] = result['atr'].rolling(window=252).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100
    )
    
    # ATR이 충분히 높을 때만 진입
    result['sufficient_volatility'] = result['atr_percentile'] > min_atr_percentile
    
    # 추가: ATR 확대 중
    result['atr_expanding'] = result['atr'] > result['atr'].rolling(window=5).mean()
    
    # 최종 진입 신호
    result['entry_signal'] = (
        result['volatility_breakout'] & 
        result['sufficient_volatility'] & 
        result['atr_expanding']
    )
    result['entry_price'] = result['target_price']
    
    return result


def composite_entry(df, k=0.5, min_score=3):
    """
    복합 진입 전략
    여러 조건의 점수를 합산하여 진입
    """
    result = df.copy()
    
    # 기본 변동성 돌파
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    result['volatility_breakout'] = result['high'] > result['target_price']
    
    # 진입 점수 계산
    result['entry_score'] = 0
    
    # 1. 기본 돌파 (2점)
    result.loc[result['volatility_breakout'], 'entry_score'] += 2
    
    # 2. 거래량 (1점)
    if 'volume' in df.columns:
        result['volume_ma'] = result['volume'].rolling(window=20).mean()
        result.loc[result['volume'] > result['volume_ma'] * 1.3, 'entry_score'] += 1
    
    # 3. 추세 (1점)
    result['ma20'] = result['close'].rolling(window=20).mean()
    result.loc[result['close'] > result['ma20'], 'entry_score'] += 1
    
    # 4. 모멘텀 (1점)
    result['momentum_5'] = result['close'].pct_change(periods=5)
    result.loc[result['momentum_5'] > 0.02, 'entry_score'] += 1
    
    # 5. RSI (1점)
    delta = result['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    result['rsi'] = 100 - (100 / (1 + rs))
    result.loc[(result['rsi'] > 40) & (result['rsi'] < 60), 'entry_score'] += 1
    
    # 6. 전일 강세 (1점)
    result['prev_bullish'] = result['close'].shift(1) > result['open'].shift(1)
    result.loc[result['prev_bullish'], 'entry_score'] += 1
    
    # 최종 진입 신호
    result['entry_signal'] = result['entry_score'] >= min_score
    result.loc[result['entry_signal'], 'entry_price'] = result.loc[result['entry_signal'], 'target_price']
    
    return result