"""
진입 전략과 청산 전략을 결합한 통합 백테스트 함수들
"""

import pandas as pd
import numpy as np
from .entry_strategies import *
from .exit_strategies import *
from .utils import calculate_performance_metrics


def run_backtest(df, entry_strategy, exit_strategy, entry_params=None, exit_params=None, 
                 slippage=0.0, commission=0.0, initial_capital=10000000):
    """
    진입 전략과 청산 전략을 결합한 백테스트 실행
    
    Parameters:
    - df: 주가 데이터프레임
    - entry_strategy: 진입 전략 함수
    - exit_strategy: 청산 전략 함수
    - entry_params: 진입 전략 파라미터 (dict)
    - exit_params: 청산 전략 파라미터 (dict)
    - slippage: 슬리피지 비율
    - commission: 수수료 비율
    - initial_capital: 초기 자본금
    
    Returns:
    - DataFrame: 백테스트 결과
    """
    # 진입 전략 실행
    if entry_params is None:
        entry_params = {}
    entry_result = entry_strategy(df, **entry_params)
    
    # 청산 전략 실행
    if exit_params is None:
        exit_params = {}
    result = exit_strategy(df, entry_result, **exit_params)
    
    # 거래 시뮬레이션 - 모든 컬럼을 float으로 초기화
    result['position'] = 0
    result['cash'] = float(initial_capital)
    result['stock_value'] = 0.0
    result['total_value'] = float(initial_capital)
    result['returns'] = 0.0
    result['trade_returns'] = 0.0
    result['shares'] = 0
    
    position_open = False
    entry_price = 0
    entry_date = None
    shares = 0
    
    for i in range(1, len(result)):
        # 전일 총자산으로 시작
        result.iloc[i, result.columns.get_loc('cash')] = float(result.iloc[i-1]['cash'])
        result.iloc[i, result.columns.get_loc('shares')] = result.iloc[i-1]['shares']
        
        # 진입 신호 확인
        if result.iloc[i-1].get('entry_signal', False) and not position_open:
            # 매수
            position_open = True
            
            # entry_price 가져오기 (여러 가능성 체크)
            if not pd.isna(result.iloc[i].get('entry_price', np.nan)):
                entry_price = result.iloc[i]['entry_price']
            elif not pd.isna(result.iloc[i-1].get('target_price', np.nan)):
                entry_price = result.iloc[i-1]['target_price']
            else:
                entry_price = result.iloc[i]['open']
                
            entry_price = entry_price * (1 + slippage)  # 슬리피지 적용
            entry_date = result.index[i]
            
            # 주식 수 계산 (전체 자금 사용)
            available_cash = result.iloc[i]['cash']
            
            if pd.isna(entry_price) or entry_price <= 0:
                continue  # 유효하지 않은 가격이면 스킵
                
            shares = int(available_cash / entry_price)
            
            if shares > 0:
                # 매수 처리
                result.iloc[i, result.columns.get_loc('position')] = 1
                result.iloc[i, result.columns.get_loc('shares')] = shares
                result.iloc[i, result.columns.get_loc('cash')] = float(available_cash - (shares * entry_price * (1 + commission)))
                
        elif position_open:
            # 포지션 보유 중
            result.iloc[i, result.columns.get_loc('position')] = 1
            
            # 청산 신호 확인
            if result.iloc[i].get('exit_signal', False):
                # 매도
                exit_price = result.iloc[i]['close'] * (1 - slippage)  # 슬리피지 적용
                
                # 매도 처리
                sell_value = shares * exit_price * (1 - commission)
                result.iloc[i, result.columns.get_loc('cash')] = float(result.iloc[i]['cash'] + sell_value)
                result.iloc[i, result.columns.get_loc('shares')] = 0
                result.iloc[i, result.columns.get_loc('position')] = 0
                
                # 거래 수익률 계산
                trade_return = (exit_price - entry_price) / entry_price - (2 * commission)
                result.iloc[i, result.columns.get_loc('trade_returns')] = trade_return
                
                position_open = False
                shares = 0
        
        # 주식 가치 계산
        result.iloc[i, result.columns.get_loc('stock_value')] = float(result.iloc[i]['shares'] * result.iloc[i]['close'])
        
        # 총 자산 계산
        result.iloc[i, result.columns.get_loc('total_value')] = float(result.iloc[i]['cash'] + result.iloc[i]['stock_value'])
        
        # 일일 수익률 계산
        if i > 0:
            result.iloc[i, result.columns.get_loc('returns')] = (
                result.iloc[i]['total_value'] - result.iloc[i-1]['total_value']
            ) / result.iloc[i-1]['total_value']
    
    # 누적 수익률 계산
    result['cumulative_returns'] = result['total_value'] / initial_capital
    
    # Buy & Hold 수익률
    result['buy_hold_returns'] = result['close'] / result['close'].iloc[0]
    
    return result


def volatility_breakout_next_day_exit(df, k=0.5, slippage=0.0, commission=0.0):
    """
    변동성 돌파 매수 + 익일 매도 전략
    
    Parameters:
    - df: 주가 데이터프레임
    - k: K값 (기본 0.5)
    - slippage: 슬리피지 비율
    - commission: 수수료 비율
    
    Returns:
    - DataFrame: 백테스트 결과
    """
    result = df.copy()
    
    # 전일 Range 계산
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    
    # 진입가 계산 (당일 시가 + 전일 Range × K)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    
    # 변동성 돌파 신호 (entry_signal과 buy_signal 둘 다 생성)
    result['entry_signal'] = result['high'] > result['target_price']
    result['buy_signal'] = result['entry_signal']  # 호환성을 위해
    
    # 매수가와 매도가 (슬리피지 적용)
    result['entry_price'] = result['target_price'] * (1 + slippage)
    result['buy_price'] = result['entry_price']  # 호환성을 위해
    result['sell_price'] = result['open'].shift(-1) * (1 - slippage) if slippage > 0 else result['open'].shift(-1)
    
    # 수익률 계산
    result['returns'] = 0.0
    buy_condition = result['entry_signal'] == True
    
    if commission > 0:
        result.loc[buy_condition, 'returns'] = (
            (result.loc[buy_condition, 'sell_price'] - result.loc[buy_condition, 'entry_price']) / 
            result.loc[buy_condition, 'entry_price'] - (2 * commission)
        )
    else:
        result.loc[buy_condition, 'returns'] = (
            (result.loc[buy_condition, 'sell_price'] - result.loc[buy_condition, 'entry_price']) / 
            result.loc[buy_condition, 'entry_price']
        )
    
    # 보유일수는 항상 1일
    result['holding_days'] = 0
    result.loc[buy_condition, 'holding_days'] = 1
    
    # 누적 수익률 계산
    result['cumulative_returns'] = (1 + result['returns']).cumprod()
    
    # Buy & Hold 수익률
    result['buy_hold_returns'] = result['close'] / result['close'].iloc[0]
    
    # 거래 횟수 (전체 데이터프레임에 대한 합계)
    result['num_trades'] = buy_condition.sum()
    
    return result


def compare_entry_strategies(df, k_values=[0.3, 0.5, 0.7], strategies=None):
    """
    여러 진입 전략 비교
    
    Parameters:
    - df: 주가 데이터프레임
    - k_values: 테스트할 K값 리스트
    - strategies: 비교할 전략 리스트 (None이면 모든 전략)
    
    Returns:
    - dict: 전략별 결과
    """
    if strategies is None:
        strategies = [
            ('기본 변동성 돌파', volatility_breakout_entry),
            ('적응형 K값', adaptive_k_entry),
            ('이중 돌파', double_breakout_entry),
            ('거래량 확인', volume_confirmed_entry),
            ('모멘텀 필터', momentum_filtered_entry),
            ('갭 조정', gap_adjusted_entry),
            ('패턴 기반', pattern_based_entry),
            ('멀티타임프레임', multi_timeframe_entry),
            ('ATR 필터', atr_filtered_entry),
            ('복합 점수', composite_entry)
        ]
    
    results = {}
    
    for strategy_name, strategy_func in strategies:
        best_k = None
        best_performance = -float('inf')
        best_result = None
        
        for k in k_values:
            # 진입 전략 실행
            if strategy_func == adaptive_k_entry:
                entry_result = strategy_func(df, k_min=k-0.2, k_max=k+0.2)
            elif strategy_func == double_breakout_entry:
                entry_result = strategy_func(df, k1=k, k2=k+0.2)
            elif strategy_func == composite_entry:
                entry_result = strategy_func(df, k=k, min_score=3)
            else:
                entry_result = strategy_func(df, k=k)
            
            # 익일 매도 적용
            exit_result = next_day_exit(df, entry_result)
            
            # 간단한 백테스트
            final_result = run_backtest(
                df, 
                lambda x, **kwargs: entry_result,  # 이미 계산된 결과 사용
                lambda x, y, **kwargs: exit_result,  # 이미 계산된 결과 사용
                slippage=0.002,
                commission=0.001
            )
            
            # 성과 평가
            total_return = final_result['cumulative_returns'].iloc[-1] - 1
            
            if total_return > best_performance:
                best_performance = total_return
                best_k = k
                best_result = final_result
        
        results[strategy_name] = {
            'result': best_result,
            'best_k': best_k,
            'total_return': best_performance,
            'metrics': calculate_performance_metrics(best_result['returns'])
        }
    
    return results


def compare_exit_strategies(df, entry_k=0.5, strategies=None):
    """
    동일한 진입 조건에서 여러 청산 전략 비교
    
    Parameters:
    - df: 주가 데이터프레임  
    - entry_k: 진입 K값
    - strategies: 비교할 청산 전략 리스트
    
    Returns:
    - dict: 전략별 결과
    """
    if strategies is None:
        strategies = [
            ('익일 매도', next_day_exit, {}),
            ('ATR 기반', atr_based_exit, {'take_profit_atr': 2.0, 'stop_loss_atr': 1.0}),
            ('이동평균선', ma_based_exit, {'short_ma': 5, 'long_ma': 20}),
            ('모멘텀 점수', momentum_score_exit, {'min_score': 2}),
            ('변동성 기반', volatility_based_exit, {'high_vol_multiplier': 1.2}),
            ('부분 익절', partial_profit_exit, {'profit_levels': [0.03, 0.05, 0.08]}),
            ('시간 가중', time_weighted_exit, {'max_days': [1, 2, 3, 4]}),
            ('볼린저 밴드', bollinger_exit, {'bb_period': 20, 'bb_std': 2}),
            ('ADX 추세', adx_trend_exit, {'strong_trend_adx': 25}),
            ('패턴 기반', pattern_based_exit, {'consecutive_up_days': 3}),
            ('복합 점수', composite_score_exit, {'min_score': 60})
        ]
    
    # 공통 진입 전략 적용
    entry_result = volatility_breakout_entry(df, k=entry_k)
    
    results = {}
    
    for strategy_name, strategy_func, params in strategies:
        # 청산 전략 적용
        exit_result = strategy_func(df, entry_result, **params)
        
        # 백테스트 실행
        final_result = run_backtest(
            df,
            lambda x, **kwargs: entry_result,  # 이미 계산된 결과 사용
            lambda x, y, **kwargs: exit_result,  # 이미 계산된 결과 사용
            slippage=0.002,
            commission=0.001
        )
        
        # 평균 보유일수 계산
        trades_with_holding = exit_result[exit_result['exit_signal'] == True]
        avg_holding_days = trades_with_holding['holding_days'].mean() if len(trades_with_holding) > 0 else 0
        
        results[strategy_name] = {
            'result': final_result,
            'total_return': final_result['cumulative_returns'].iloc[-1] - 1,
            'avg_holding_days': avg_holding_days,
            'num_trades': (exit_result['exit_signal'] == True).sum(),
            'metrics': calculate_performance_metrics(final_result['returns'])
        }
    
    return results