"""
간단한 백테스트 함수 - 디버깅 및 기본 사용을 위한 버전
"""

import pandas as pd
import numpy as np


def simple_backtest_entry_exit(df, entry_result, exit_result, slippage=0.0, commission=0.0):
    """
    진입/청산 결과를 받아서 간단하게 백테스트 수행
    
    Parameters:
    - df: 원본 가격 데이터
    - entry_result: 진입 전략 결과 (entry_signal, entry_price 포함)
    - exit_result: 청산 전략 결과 (exit_signal 포함)
    - slippage: 슬리피지
    - commission: 수수료
    
    Returns:
    - DataFrame: 백테스트 결과
    """
    result = df.copy()
    
    # entry와 exit 결과 병합
    for col in entry_result.columns:
        if col not in result.columns:
            result[col] = entry_result[col]
    
    for col in exit_result.columns:
        if col not in result.columns:
            result[col] = exit_result[col]
    
    # 백테스트 변수 초기화
    result['position'] = 0
    result['returns'] = 0.0
    result['trade_returns'] = 0.0
    
    position_open = False
    entry_price = 0
    entry_idx = 0
    
    for i in range(1, len(result)):
        # 진입 신호
        if not position_open and result.iloc[i-1].get('entry_signal', False):
            position_open = True
            entry_idx = i
            
            # 진입 가격 결정
            if 'entry_price' in result.columns and not pd.isna(result.iloc[i]['entry_price']):
                entry_price = result.iloc[i]['entry_price']
            elif 'target_price' in result.columns and not pd.isna(result.iloc[i-1]['target_price']):
                entry_price = result.iloc[i-1]['target_price']
            else:
                entry_price = result.iloc[i]['open']
            
            entry_price = entry_price * (1 + slippage)
            result.iloc[i, result.columns.get_loc('position')] = 1
            
        elif position_open:
            result.iloc[i, result.columns.get_loc('position')] = 1
            
            # 청산 신호
            if result.iloc[i].get('exit_signal', False):
                exit_price = result.iloc[i]['close'] * (1 - slippage)
                
                # 수익률 계산
                trade_return = (exit_price - entry_price) / entry_price - (2 * commission)
                result.iloc[i, result.columns.get_loc('trade_returns')] = trade_return
                result.iloc[i, result.columns.get_loc('returns')] = trade_return
                
                position_open = False
    
    # 누적 수익률
    result['cumulative_returns'] = (1 + result['returns']).cumprod()
    
    # Buy & Hold
    result['buy_hold_returns'] = result['close'] / result['close'].iloc[0]
    
    # 거래 통계
    trades = result[result['trade_returns'] != 0]
    result['total_trades'] = len(trades)
    result['win_rate'] = (trades['trade_returns'] > 0).mean() if len(trades) > 0 else 0
    result['avg_win'] = trades[trades['trade_returns'] > 0]['trade_returns'].mean() if len(trades[trades['trade_returns'] > 0]) > 0 else 0
    result['avg_loss'] = trades[trades['trade_returns'] < 0]['trade_returns'].mean() if len(trades[trades['trade_returns'] < 0]) > 0 else 0
    
    return result


def simple_volatility_breakout_backtest(df, k=0.5, slippage=0.002, commission=0.001):
    """
    간단한 변동성 돌파 전략 백테스트
    
    Parameters:
    - df: 가격 데이터
    - k: K값
    - slippage: 슬리피지
    - commission: 수수료
    
    Returns:
    - DataFrame: 백테스트 결과
    """
    result = df.copy()
    
    # 변동성 돌파 계산
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    result['signal'] = result['high'] > result['target_price']
    
    # 수익률 계산
    result['returns'] = 0.0
    
    for i in range(1, len(result)-1):
        if result.iloc[i]['signal']:
            # 진입가: 목표가에 슬리피지 추가
            entry = result.iloc[i]['target_price'] * (1 + slippage)
            # 청산가: 익일 시가에 슬리피지 차감
            exit = result.iloc[i+1]['open'] * (1 - slippage)
            # 수익률
            ret = (exit - entry) / entry - (2 * commission)
            result.iloc[i, result.columns.get_loc('returns')] = ret
    
    # 누적 수익률
    result['cumulative_returns'] = (1 + result['returns']).cumprod()
    
    # Buy & Hold
    result['buy_hold_returns'] = result['close'] / result['close'].iloc[0]
    
    # 통계
    result['num_trades'] = result['signal'].sum()
    trades = result[result['returns'] != 0]
    result['win_rate'] = (trades['returns'] > 0).mean() if len(trades) > 0 else 0
    
    return result