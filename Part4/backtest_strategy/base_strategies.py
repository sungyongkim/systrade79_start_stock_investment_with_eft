"""
기본 변동성 돌파 전략 및 필터 적용 전략
"""

import pandas as pd
import numpy as np


def calculate_atr(df, period=14):
    """
    ATR (Average True Range) 계산
    
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
    
    # ATR 계산 (단순이동평균)
    atr = tr.rolling(window=period).mean()
    
    return atr


def volatility_breakout_base(df, k=0.5, slippage=0.0, commission=0.0):
    """
    기본 변동성 돌파 전략 (익일 매도)
    
    Parameters:
    - df: 주가 데이터프레임
    - k: K값 (기본 0.5)
    - slippage: 슬리피지 비율 (기본 0.0)
    - commission: 수수료 비율 (기본 0.0)
    
    Returns:
    - DataFrame: 백테스팅 결과
    """
    result = df.copy()
    
    # 전일 Range 계산
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    
    # 진입가 계산 (당일 시가 + 전일 Range × K)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    
    # 변동성 돌파 신호
    result['buy_signal'] = result['high'] > result['target_price']
    
    # 매수가와 매도가 (슬리피지 적용)
    result['buy_price'] = result['target_price'] * (1 + slippage)
    result['sell_price'] = result['open'].shift(-1) * (1 - slippage) if slippage > 0 else result['open'].shift(-1)
    
    # 수익률 계산
    result['returns'] = 0.0
    buy_condition = result['buy_signal'] == True
    
    if commission > 0:
        result.loc[buy_condition, 'returns'] = (
            (result.loc[buy_condition, 'sell_price'] - result.loc[buy_condition, 'buy_price']) / 
            result.loc[buy_condition, 'buy_price'] - (2 * commission)
        )
    else:
        result.loc[buy_condition, 'returns'] = (
            (result.loc[buy_condition, 'sell_price'] - result.loc[buy_condition, 'buy_price']) / 
            result.loc[buy_condition, 'buy_price']
        )
    
    # 누적 수익률 계산
    result['cumulative_returns'] = (1 + result['returns']).cumprod()
    
    # Buy & Hold 수익률
    result['buy_hold_returns'] = result['close'] / result['close'].iloc[0]
    
    return result


def volatility_breakout_with_filters(df, k=0.5, adx_threshold=20, 
                                    momentum_threshold=0.0, use_atr_filter=True,
                                    slippage=0.0, commission=0.0):
    """
    변동성 돌파 + 필터 적용 전략
    
    Parameters:
    - df: 주가 데이터프레임 (ADX, Chaikin, 모멘텀 포함 필요)
    - k: K값 (기본 0.5)
    - adx_threshold: ADX 임계값 (기본 20)
    - momentum_threshold: 절대 모멘텀 임계값 (기본 0.0)
    - use_atr_filter: ATR 필터 사용 여부 (기본 True)
    - slippage: 슬리피지 비율 (기본 0.0)
    - commission: 수수료 비율 (기본 0.0)
    
    Returns:
    - DataFrame: 백테스팅 결과
    """
    result = df.copy()
    
    # 전일 Range 계산
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    
    # 진입가 계산
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    
    # 변동성 돌파 신호
    result['volatility_signal'] = result['high'] > result['target_price']
    
    # ADX 필터 (옵션)
    if 'adx_14' in df.columns:
        result['adx_filter'] = (
            (result['adx_14'] > adx_threshold) & 
            (result.get('pdi_14', 0) > result.get('mdi_14', 0))
        )
    else:
        result['adx_filter'] = True
    
    # Chaikin 필터 (옵션)
    if 'chaikin_oscillator' in df.columns:
        result['chaikin_filter'] = (
            (result['adx_14'] < adx_threshold) & 
            ((result['chaikin_oscillator'] > result.get('chaikin_signal', 0)) | 
             (result['chaikin_oscillator'] > result['chaikin_oscillator'].shift(1)))
        )
    else:
        result['chaikin_filter'] = False
    
    # 절대 모멘텀 필터 (옵션)
    if 'momentum_20' not in df.columns:
        result['momentum_20'] = result['close'].pct_change(periods=20)
    result['momentum_filter'] = result['momentum_20'] > momentum_threshold
    
    # ATR 필터 (옵션)
    if use_atr_filter:
        result['atr'] = calculate_atr(df)
        result['atr_ma'] = result['atr'].rolling(window=14).mean()
        result['atr_filter'] = result['atr'] > result['atr_ma']
    else:
        result['atr_filter'] = True
    
    # 최종 매수 신호
    result['buy_signal'] = (
        result['volatility_signal'] & 
        ((result['adx_filter'] & result['momentum_filter'] & result['atr_filter']) | 
         result['chaikin_filter'])
    )
    
    # 매수가와 매도가 (익일 매도 기본)
    result['buy_price'] = result['target_price'] * (1 + slippage)
    result['sell_price'] = result['open'].shift(-1) * (1 - slippage) if slippage > 0 else result['open'].shift(-1)
    
    # 수익률 계산
    result['returns'] = 0.0
    buy_condition = result['buy_signal'] == True
    
    if commission > 0:
        result.loc[buy_condition, 'returns'] = (
            (result.loc[buy_condition, 'sell_price'] - result.loc[buy_condition, 'buy_price']) / 
            result.loc[buy_condition, 'buy_price'] - (2 * commission)
        )
    else:
        result.loc[buy_condition, 'returns'] = (
            (result.loc[buy_condition, 'sell_price'] - result.loc[buy_condition, 'buy_price']) / 
            result.loc[buy_condition, 'buy_price']
        )
    
    # 누적 수익률
    result['cumulative_returns'] = (1 + result['returns']).cumprod()
    
    # Buy & Hold
    result['buy_hold_returns'] = result['close'] / result['close'].iloc[0]
    
    return result