"""
전략 비교를 위한 개선된 함수들
각 전략의 특성에 맞는 파라미터 설정
"""

import pandas as pd
import numpy as np
from .entry_strategies import *
from .exit_strategies import *
from .simple_backtest import simple_backtest_entry_exit
from .utils import calculate_performance_metrics


def get_entry_strategies_with_params(k_base=0.5):
    """
    각 진입 전략과 적절한 파라미터를 반환
    
    Parameters:
    - k_base: 기준 K값
    
    Returns:
    - list: (전략명, 함수, 파라미터) 튜플의 리스트
    """
    strategies = [
        ('기본 변동성 돌파', volatility_breakout_entry, {'k': k_base}),
        ('적응형 K값', adaptive_k_entry, {'k_min': k_base-0.2, 'k_max': k_base+0.2}),
        ('이중 돌파', double_breakout_entry, {'k1': k_base, 'k2': k_base+0.2}),
        ('거래량 확인', volume_confirmed_entry, {'k': k_base, 'volume_multiplier': 1.5}),
        ('모멘텀 필터', momentum_filtered_entry, {'k': k_base, 'momentum_threshold': 0.02}),
        ('갭 조정', gap_adjusted_entry, {'k': k_base, 'gap_threshold': 0.02}),
        ('패턴 기반', pattern_based_entry, {'k': k_base, 'pattern_lookback': 3}),
        ('멀티타임프레임', multi_timeframe_entry, {'k': k_base, 'confirm_periods': [5, 20]}),
        ('ATR 필터', atr_filtered_entry, {'k': k_base, 'min_atr_percentile': 30}),
        ('복합 점수', composite_entry, {'k': k_base, 'min_score': 3})
    ]
    return strategies


def get_exit_strategies_with_params():
    """
    각 청산 전략과 적절한 파라미터를 반환
    
    Returns:
    - list: (전략명, 함수, 파라미터) 튜플의 리스트
    """
    strategies = [
        ('익일 매도', next_day_exit, {}),
        ('ATR 기반', atr_based_exit, {
            'take_profit_atr': 2.0, 
            'stop_loss_atr': 1.0,
            'trailing_stop_atr': 1.5,
            'max_holding_days': 20
        }),
        ('이동평균선', ma_based_exit, {
            'short_ma': 5, 
            'long_ma': 20,
            'max_holding_days': 20
        }),
        ('모멘텀 점수', momentum_score_exit, {
            'min_score': 2,
            'max_holding_days': 10
        }),
        ('변동성 기반', volatility_based_exit, {
            'high_vol_multiplier': 1.2,
            'low_vol_multiplier': 0.8,
            'max_holding_days': 15
        }),
        ('부분 익절', partial_profit_exit, {
            'profit_levels': [0.03, 0.05, 0.08],
            'sell_ratios': [0.3, 0.3, 0.2],
            'stop_loss': -0.02
        }),
        ('시간 가중', time_weighted_exit, {
            'loss_thresholds': [-0.00, -0.01, -0.02, -0.03],
            'max_days': [1, 2, 3, 4],
            'exceptional_return': 0.05
        }),
        ('볼린저 밴드', bollinger_exit, {
            'bb_period': 20,
            'bb_std': 2,
            'max_holding_days': 15
        }),
        ('ADX 추세', adx_trend_exit, {
            'strong_trend_adx': 25,
            'weak_trend_adx': 20,
            'strong_trend_days': 10,
            'weak_trend_days': 5
        }),
        ('패턴 기반', pattern_based_exit, {
            'consecutive_up_days': 3,
            'max_holding_days': 5
        }),
        ('복합 점수', composite_score_exit, {
            'min_score': 60,
            'max_holding_days': 10
        })
    ]
    return strategies


def compare_all_entry_strategies(df, k_values=[0.3, 0.5, 0.7], slippage=0.002, commission=0.001):
    """
    모든 진입 전략을 비교 (익일 매도 기준)
    
    Parameters:
    - df: 가격 데이터
    - k_values: 테스트할 K값들
    - slippage: 슬리피지
    - commission: 수수료
    
    Returns:
    - DataFrame: 비교 결과
    """
    results = []
    
    for strategy_name, strategy_func, base_params in get_entry_strategies_with_params(0.5):
        best_return = -float('inf')
        best_k = None
        best_trades = 0
        best_win_rate = 0
        
        # 각 K값에 대해 테스트
        for k in k_values:
            # K값에 따라 파라미터 조정
            params = base_params.copy()
            if 'k' in params:
                params['k'] = k
            elif 'k_min' in params:
                params['k_min'] = k - 0.2
                params['k_max'] = k + 0.2
            elif 'k1' in params:
                params['k1'] = k
                params['k2'] = k + 0.2
            
            try:
                # 진입 전략 실행
                entry_result = strategy_func(df, **params)
                
                # 익일 매도
                exit_result = next_day_exit(df, entry_result)
                
                # 백테스트
                final_result = simple_backtest_entry_exit(
                    df, entry_result, exit_result, 
                    slippage=slippage, commission=commission
                )
                
                total_return = (final_result['cumulative_returns'].iloc[-1] - 1) * 100
                num_trades = final_result['total_trades'].iloc[0]
                win_rate = final_result['win_rate'].iloc[0] * 100
                
                if total_return > best_return:
                    best_return = total_return
                    best_k = k
                    best_trades = num_trades
                    best_win_rate = win_rate
                    
            except Exception as e:
                print(f"⚠️ {strategy_name} 실행 중 오류: {e}")
                continue
        
        results.append({
            '전략': strategy_name,
            '최적 K값': best_k,
            '수익률(%)': round(best_return, 2),
            '거래횟수': best_trades,
            '승률(%)': round(best_win_rate, 1)
        })
    
    return pd.DataFrame(results).sort_values('수익률(%)', ascending=False)


def compare_all_exit_strategies(df, entry_k=0.5, slippage=0.002, commission=0.001):
    """
    모든 청산 전략을 비교 (변동성 돌파 진입 기준)
    
    Parameters:
    - df: 가격 데이터
    - entry_k: 진입 K값
    - slippage: 슬리피지
    - commission: 수수료
    
    Returns:
    - DataFrame: 비교 결과
    """
    results = []
    
    # 공통 진입 전략
    entry_result = volatility_breakout_entry(df, k=entry_k)
    
    for strategy_name, strategy_func, params in get_exit_strategies_with_params():
        try:
            # 청산 전략 실행
            exit_result = strategy_func(df, entry_result, **params)
            
            # 백테스트
            final_result = simple_backtest_entry_exit(
                df, entry_result, exit_result,
                slippage=slippage, commission=commission
            )
            
            # 평균 보유일수 계산
            exits = exit_result[exit_result['exit_signal'] == True]
            avg_holding = exits['holding_days'].mean() if len(exits) > 0 and 'holding_days' in exits.columns else 1
            
            # 성과 지표
            total_return = (final_result['cumulative_returns'].iloc[-1] - 1) * 100
            num_trades = final_result['total_trades'].iloc[0]
            win_rate = final_result.get('win_rate', pd.Series([0])).iloc[0] * 100
            
            # 추가 지표
            metrics = calculate_performance_metrics(final_result['returns'])
            
            results.append({
                '전략': strategy_name,
                '수익률(%)': round(total_return, 2),
                '거래횟수': num_trades,
                '평균보유일': round(avg_holding, 1),
                '승률(%)': round(win_rate, 1),
                '샤프비율': metrics.get('샤프비율', 'N/A'),
                '최대낙폭': metrics.get('최대낙폭', 'N/A')
            })
            
        except Exception as e:
            print(f"⚠️ {strategy_name} 실행 중 오류: {e}")
            continue
    
    return pd.DataFrame(results).sort_values('수익률(%)', ascending=False)


def find_best_combination(df, top_n=3, slippage=0.002, commission=0.001):
    """
    최적의 진입/청산 전략 조합 찾기
    
    Parameters:
    - df: 가격 데이터
    - top_n: 상위 n개 조합
    - slippage: 슬리피지
    - commission: 수수료
    
    Returns:
    - DataFrame: 최적 조합 결과
    """
    results = []
    
    # 상위 진입 전략 선택
    entry_strategies = get_entry_strategies_with_params(0.5)[:5]  # 상위 5개만
    exit_strategies = get_exit_strategies_with_params()[:5]  # 상위 5개만
    
    for entry_name, entry_func, entry_params in entry_strategies:
        for exit_name, exit_func, exit_params in exit_strategies:
            try:
                # 진입 전략
                entry_result = entry_func(df, **entry_params)
                
                # 청산 전략
                exit_result = exit_func(df, entry_result, **exit_params)
                
                # 백테스트
                final_result = simple_backtest_entry_exit(
                    df, entry_result, exit_result,
                    slippage=slippage, commission=commission
                )
                
                total_return = (final_result['cumulative_returns'].iloc[-1] - 1) * 100
                
                results.append({
                    '진입전략': entry_name,
                    '청산전략': exit_name,
                    '수익률(%)': round(total_return, 2)
                })
                
            except Exception as e:
                continue
    
    results_df = pd.DataFrame(results).sort_values('수익률(%)', ascending=False)
    return results_df.head(top_n)