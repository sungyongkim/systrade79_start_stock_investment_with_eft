"""
다양한 청산(Exit) 전략 구현
"""

import pandas as pd
import numpy as np
from .base_strategies import calculate_atr


def next_day_exit(df, entry_result):
    """
    익일 매도 전략 (기본)
    
    Parameters:
    - df: 원본 데이터
    - entry_result: 진입 신호가 포함된 결과 DataFrame
    
    Returns:
    - DataFrame: 청산 신호가 추가된 결과
    """
    result = entry_result.copy()
    
    # 익일 시가 매도 (이미 base_strategies에서 구현됨)
    buy_signal_col = 'buy_signal' if 'buy_signal' in result.columns else 'entry_signal'
    result['exit_signal'] = result[buy_signal_col].shift(1).astype(bool).fillna(False)
    result['holding_days'] = 1  # 항상 1일 보유
    
    return result


def atr_based_exit(df, entry_result, take_profit_atr=2.0, stop_loss_atr=1.0, 
                   trailing_stop_atr=1.5, max_holding_days=20):
    """
    ATR 기반 동적 익절/손절 전략
    
    Parameters:
    - take_profit_atr: 익절선 ATR 배수
    - stop_loss_atr: 손절선 ATR 배수
    - trailing_stop_atr: 추적손절 ATR 배수
    - max_holding_days: 최대 보유일수
    """
    result = entry_result.copy()
    
    # ATR 계산
    if 'atr' not in result.columns:
        result['atr'] = calculate_atr(df)
    
    # 포지션 추적
    result['position'] = 0
    result['entry_price'] = np.nan
    result['entry_atr'] = np.nan
    result['highest_price'] = np.nan
    result['holding_days'] = 0
    result['exit_signal'] = False
    result['exit_reason'] = ''
    
    position_open = False
    
    for i in range(1, len(result)):
        if result.iloc[i-1].get('buy_signal', result.iloc[i-1].get('entry_signal', False)) and not position_open:
            # 진입
            position_open = True
            result.iloc[i, result.columns.get_loc('position')] = 1
            # 진입 가격 설정
            if not pd.isna(result.iloc[i].get('entry_price', np.nan)):
                entry_price_val = result.iloc[i]['entry_price']
            elif not pd.isna(result.iloc[i].get('buy_price', np.nan)):
                entry_price_val = result.iloc[i]['buy_price']
            elif not pd.isna(result.iloc[i-1].get('target_price', np.nan)):
                entry_price_val = result.iloc[i-1]['target_price']
            else:
                entry_price_val = result.iloc[i]['open']
            result.iloc[i, result.columns.get_loc('entry_price')] = entry_price_val
            result.iloc[i, result.columns.get_loc('entry_atr')] = result.iloc[i]['atr']
            result.iloc[i, result.columns.get_loc('highest_price')] = result.iloc[i]['high']
            result.iloc[i, result.columns.get_loc('holding_days')] = 1
            
        elif position_open:
            # 포지션 보유 중
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('entry_price')] = result.iloc[i-1]['entry_price']
            result.iloc[i, result.columns.get_loc('entry_atr')] = result.iloc[i-1]['entry_atr']
            result.iloc[i, result.columns.get_loc('holding_days')] = result.iloc[i-1]['holding_days'] + 1
            
            # 최고가 갱신
            prev_highest = result.iloc[i-1]['highest_price']
            current_high = result.iloc[i]['high']
            result.iloc[i, result.columns.get_loc('highest_price')] = max(prev_highest, current_high)
            
            # 청산 조건 체크
            entry_price = result.iloc[i]['entry_price']
            entry_atr = result.iloc[i]['entry_atr']
            
            # 익절 체크
            take_profit_price = entry_price + (entry_atr * take_profit_atr)
            if result.iloc[i]['high'] >= take_profit_price:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'take_profit'
                position_open = False
                continue
            
            # 손절 체크
            stop_loss_price = entry_price - (entry_atr * stop_loss_atr)
            if result.iloc[i]['low'] <= stop_loss_price:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'stop_loss'
                position_open = False
                continue
            
            # 추적 손절 체크
            trailing_stop_price = result.iloc[i]['highest_price'] - (result.iloc[i]['atr'] * trailing_stop_atr)
            if result.iloc[i]['low'] <= trailing_stop_price:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'trailing_stop'
                position_open = False
                continue
            
            # 최대 보유일수 체크
            if result.iloc[i]['holding_days'] >= max_holding_days:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'max_days'
                position_open = False
    
    return result


def ma_based_exit(df, entry_result, short_ma=5, long_ma=20, max_holding_days=20):
    """
    이동평균선 기반 보유 전략
    
    보유 조건: 종가 > MA5 and MA5 > MA20
    """
    result = entry_result.copy()
    
    # 이동평균 계산
    result['ma_short'] = result['close'].rolling(window=short_ma).mean()
    result['ma_long'] = result['close'].rolling(window=long_ma).mean()
    
    # 포지션 추적
    result['position'] = 0
    result['holding_days'] = 0
    result['exit_signal'] = False
    result['exit_reason'] = ''
    
    position_open = False
    
    for i in range(1, len(result)):
        if result.iloc[i-1].get('buy_signal', result.iloc[i-1].get('entry_signal', False)) and not position_open:
            position_open = True
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = 1
            
        elif position_open:
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = result.iloc[i-1]['holding_days'] + 1
            
            # 청산 조건
            if (result.iloc[i]['close'] < result.iloc[i]['ma_short'] or 
                result.iloc[i]['ma_short'] < result.iloc[i]['ma_long']):
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'ma_cross'
                position_open = False
            elif result.iloc[i]['holding_days'] >= max_holding_days:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'max_days'
                position_open = False
    
    return result


def momentum_score_exit(df, entry_result, min_score=2, max_holding_days=10):
    """
    모멘텀 점수 기반 전략
    """
    result = entry_result.copy()
    
    # 모멘텀 지표 계산
    result['momentum_score'] = 0
    
    # 1. 당일 수익률 > 0
    result['daily_return'] = result['close'].pct_change()
    result.loc[result['daily_return'] > 0, 'momentum_score'] += 1
    
    # 2. 종가 > 5일 고가
    result['high_5d'] = result['high'].rolling(window=5).max()
    result.loc[result['close'] > result['high_5d'].shift(1), 'momentum_score'] += 1
    
    # 3. 거래량 > 20일 평균
    if 'volume' in result.columns:
        result['volume_ma20'] = result['volume'].rolling(window=20).mean()
        result.loc[result['volume'] > result['volume_ma20'] * 1.2, 'momentum_score'] += 1
    
    # 4. RSI > 50
    # RSI 계산 (간단한 버전)
    delta = result['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    result['rsi'] = 100 - (100 / (1 + rs))
    result.loc[result['rsi'] > 50, 'momentum_score'] += 1
    
    # 포지션 추적
    result['position'] = 0
    result['holding_days'] = 0
    result['exit_signal'] = False
    result['exit_reason'] = ''
    
    position_open = False
    
    for i in range(1, len(result)):
        if result.iloc[i-1].get('buy_signal', result.iloc[i-1].get('entry_signal', False)) and not position_open:
            position_open = True
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = 1
            
        elif position_open:
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = result.iloc[i-1]['holding_days'] + 1
            
            # 청산 조건
            if result.iloc[i]['momentum_score'] < min_score:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'low_momentum'
                position_open = False
            elif result.iloc[i]['holding_days'] >= max_holding_days:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'max_days'
                position_open = False
    
    return result


def volatility_based_exit(df, entry_result, high_vol_multiplier=1.2, 
                         low_vol_multiplier=0.8, max_holding_days=15):
    """
    변동성 확대/축소 기반 전략
    """
    result = entry_result.copy()
    
    # ATR 계산
    if 'atr' not in result.columns:
        result['atr'] = calculate_atr(df)
    
    result['atr_ma'] = result['atr'].rolling(window=20).mean()
    
    # 포지션 추적
    result['position'] = 0
    result['holding_days'] = 0
    result['exit_signal'] = False
    result['exit_reason'] = ''
    result['current_return'] = 0.0
    
    position_open = False
    entry_price = 0
    
    for i in range(1, len(result)):
        if result.iloc[i-1].get('buy_signal', result.iloc[i-1].get('entry_signal', False)) and not position_open:
            position_open = True
            entry_price = result.iloc[i].get('buy_price', result.iloc[i].get('entry_price', result.iloc[i]['open']))
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = 1
            
        elif position_open:
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = result.iloc[i-1]['holding_days'] + 1
            result.iloc[i, result.columns.get_loc('current_return')] = (result.iloc[i]['close'] - entry_price) / entry_price
            
            # 청산 조건
            if result.iloc[i]['atr'] < result.iloc[i]['atr_ma'] * low_vol_multiplier:
                # 변동성 축소
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'low_volatility'
                position_open = False
            elif (result.iloc[i]['atr'] > result.iloc[i]['atr_ma'] * low_vol_multiplier and 
                  result.iloc[i]['atr'] < result.iloc[i]['atr_ma'] * high_vol_multiplier and
                  result.iloc[i]['current_return'] < 0):
                # 중간 변동성 + 손실
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'loss_in_normal_vol'
                position_open = False
            elif result.iloc[i]['holding_days'] >= max_holding_days:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'max_days'
                position_open = False
    
    return result


def partial_profit_exit(df, entry_result, profit_levels=[0.03, 0.05, 0.08], 
                       sell_ratios=[0.3, 0.3, 0.2], stop_loss=-0.02):
    """
    단계별 부분 익절 전략
    """
    result = entry_result.copy()
    
    # 포지션 추적
    result['position'] = 0.0  # 비율로 관리
    result['holding_days'] = 0
    result['exit_signal'] = False
    result['exit_reason'] = ''
    result['current_return'] = 0.0
    result['partial_exits'] = ''
    
    position_open = False
    entry_price = 0
    remaining_position = 0.0
    exits_done = []
    
    for i in range(1, len(result)):
        if result.iloc[i-1].get('buy_signal', result.iloc[i-1].get('entry_signal', False)) and not position_open:
            position_open = True
            entry_price = result.iloc[i].get('buy_price', result.iloc[i].get('entry_price', result.iloc[i]['open']))
            remaining_position = 1.0
            exits_done = []
            result.iloc[i, result.columns.get_loc('position')] = remaining_position
            result.iloc[i, result.columns.get_loc('holding_days')] = 1
            
        elif position_open and remaining_position > 0:
            result.iloc[i, result.columns.get_loc('position')] = remaining_position
            result.iloc[i, result.columns.get_loc('holding_days')] = result.iloc[i-1]['holding_days'] + 1
            result.iloc[i, result.columns.get_loc('current_return')] = (result.iloc[i]['close'] - entry_price) / entry_price
            
            current_return = result.iloc[i]['current_return']
            
            # 손절 체크
            if current_return <= stop_loss:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'stop_loss'
                result.iloc[i, result.columns.get_loc('partial_exits')] = f'전량청산({current_return:.1%})'
                position_open = False
                remaining_position = 0.0
                continue
            
            # 부분 익절 체크
            for level_idx, (profit_level, sell_ratio) in enumerate(zip(profit_levels, sell_ratios)):
                if current_return >= profit_level and level_idx not in exits_done:
                    remaining_position *= (1 - sell_ratio)
                    exits_done.append(level_idx)
                    result.iloc[i, result.columns.get_loc('partial_exits')] += f'{int(sell_ratio*100)}%익절({profit_level:.0%}) '
                    
                    if remaining_position < 0.1:  # 10% 미만 남으면 전량 청산
                        result.iloc[i, result.columns.get_loc('exit_signal')] = True
                        result.iloc[i, result.columns.get_loc('exit_reason')] = 'final_exit'
                        position_open = False
                        remaining_position = 0.0
    
    return result


def time_weighted_exit(df, entry_result, loss_thresholds=[-0.00, -0.01, -0.02, -0.03], 
                      max_days=[1, 2, 3, 4], exceptional_return=0.05):
    """
    시간 가중 청산 전략
    """
    result = entry_result.copy()
    
    # 포지션 추적
    result['position'] = 0
    result['holding_days'] = 0
    result['exit_signal'] = False
    result['exit_reason'] = ''
    result['current_return'] = 0.0
    
    position_open = False
    entry_price = 0
    
    for i in range(1, len(result)):
        if result.iloc[i-1].get('buy_signal', result.iloc[i-1].get('entry_signal', False)) and not position_open:
            position_open = True
            entry_price = result.iloc[i].get('buy_price', result.iloc[i].get('entry_price', result.iloc[i]['open']))
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = 1
            
        elif position_open:
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = result.iloc[i-1]['holding_days'] + 1
            result.iloc[i, result.columns.get_loc('current_return')] = (result.iloc[i]['close'] - entry_price) / entry_price
            
            holding_days = result.iloc[i]['holding_days']
            current_return = result.iloc[i]['current_return']
            
            # 예외 조건: 높은 수익률
            if current_return > exceptional_return and holding_days <= 10:
                continue  # 계속 보유
            
            # 시간별 청산 조건
            for day_idx, (max_day, loss_threshold) in enumerate(zip(max_days, loss_thresholds)):
                if holding_days == max_day and current_return < loss_threshold:
                    result.iloc[i, result.columns.get_loc('exit_signal')] = True
                    result.iloc[i, result.columns.get_loc('exit_reason')] = f'day{max_day}_threshold'
                    position_open = False
                    break
            
            # 최대 보유일수
            if holding_days >= max(max_days) + 1:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'max_days'
                position_open = False
    
    return result


def bollinger_exit(df, entry_result, bb_period=20, bb_std=2, max_holding_days=15):
    """
    볼린저 밴드 기반 전략
    """
    result = entry_result.copy()
    
    # 볼린저 밴드 계산
    result['bb_middle'] = result['close'].rolling(window=bb_period).mean()
    bb_std_val = result['close'].rolling(window=bb_period).std()
    result['bb_upper'] = result['bb_middle'] + (bb_std_val * bb_std)
    result['bb_lower'] = result['bb_middle'] - (bb_std_val * bb_std)
    
    # 포지션 추적
    result['position'] = 0
    result['holding_days'] = 0
    result['exit_signal'] = False
    result['exit_reason'] = ''
    result['current_return'] = 0.0
    
    position_open = False
    entry_price = 0
    
    for i in range(1, len(result)):
        if result.iloc[i-1].get('buy_signal', result.iloc[i-1].get('entry_signal', False)) and not position_open:
            position_open = True
            entry_price = result.iloc[i].get('buy_price', result.iloc[i].get('entry_price', result.iloc[i]['open']))
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = 1
            
        elif position_open:
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = result.iloc[i-1]['holding_days'] + 1
            result.iloc[i, result.columns.get_loc('current_return')] = (result.iloc[i]['close'] - entry_price) / entry_price
            
            # 청산 조건
            if result.iloc[i]['close'] < result.iloc[i]['bb_lower']:
                # 하단 밴드 이탈
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'bb_lower_break'
                position_open = False
            elif (result.iloc[i]['close'] < result.iloc[i]['bb_middle'] and 
                  result.iloc[i]['current_return'] > 0):
                # 중심선 하향 돌파 + 수익
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'bb_middle_break_profit'
                position_open = False
            elif result.iloc[i]['holding_days'] >= max_holding_days:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'max_days'
                position_open = False
    
    return result


def adx_trend_exit(df, entry_result, strong_trend_adx=25, weak_trend_adx=20, 
                   strong_trend_days=10, weak_trend_days=5):
    """
    ADX 추세 강도 기반 전략
    """
    result = entry_result.copy()
    
    # 포지션 추적
    result['position'] = 0
    result['holding_days'] = 0
    result['exit_signal'] = False
    result['exit_reason'] = ''
    result['max_holding'] = 1  # 기본 1일
    result['stop_loss_pct'] = 0.0
    
    position_open = False
    entry_price = 0
    max_holding_days = 1
    stop_loss_pct = 0.0
    
    for i in range(1, len(result)):
        if result.iloc[i-1].get('buy_signal', result.iloc[i-1].get('entry_signal', False)) and not position_open:
            position_open = True
            entry_price = result.iloc[i].get('buy_price', result.iloc[i].get('entry_price', result.iloc[i]['open']))
            
            # ADX에 따른 보유기간 설정
            if 'adx_14' in result.columns:
                adx_value = result.iloc[i]['adx_14']
                if adx_value > strong_trend_adx and result.iloc[i].get('pdi_14', 0) > result.iloc[i].get('mdi_14', 0):
                    max_holding_days = strong_trend_days
                    stop_loss_pct = 0.05
                elif adx_value > weak_trend_adx and result.iloc[i].get('pdi_14', 0) > result.iloc[i].get('mdi_14', 0):
                    max_holding_days = weak_trend_days
                    stop_loss_pct = 0.03
                else:
                    max_holding_days = 1  # 익일 청산
                    stop_loss_pct = 0.0
            
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = 1
            result.iloc[i, result.columns.get_loc('max_holding')] = max_holding_days
            result.iloc[i, result.columns.get_loc('stop_loss_pct')] = stop_loss_pct
            
        elif position_open:
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = result.iloc[i-1]['holding_days'] + 1
            result.iloc[i, result.columns.get_loc('max_holding')] = max_holding_days
            result.iloc[i, result.columns.get_loc('stop_loss_pct')] = stop_loss_pct
            
            current_return = (result.iloc[i]['close'] - entry_price) / entry_price
            
            # 손절 체크
            if stop_loss_pct > 0 and current_return <= -stop_loss_pct:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'stop_loss'
                position_open = False
            # 최대 보유일수 체크
            elif result.iloc[i]['holding_days'] >= max_holding_days:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'max_days_by_adx'
                position_open = False
    
    return result


def pattern_based_exit(df, entry_result, consecutive_up_days=3, max_holding_days=5):
    """
    패턴 인식 기반 전략
    """
    result = entry_result.copy()
    
    # 패턴 인식
    result['is_bullish'] = result['close'] > result['open']
    result['is_doji'] = abs(result['close'] - result['open']) / result['open'] < 0.001
    result['has_long_upper_shadow'] = (result['high'] - np.maximum(result['open'], result['close'])) > \
                                      (np.maximum(result['open'], result['close']) - np.minimum(result['open'], result['close'])) * 2
    
    # 포지션 추적
    result['position'] = 0
    result['holding_days'] = 0
    result['exit_signal'] = False
    result['exit_reason'] = ''
    result['current_return'] = 0.0
    
    position_open = False
    entry_price = 0
    
    for i in range(1, len(result)):
        if result.iloc[i-1].get('buy_signal', result.iloc[i-1].get('entry_signal', False)) and not position_open:
            position_open = True
            entry_price = result.iloc[i].get('buy_price', result.iloc[i].get('entry_price', result.iloc[i]['open']))
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = 1
            
        elif position_open:
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = result.iloc[i-1]['holding_days'] + 1
            result.iloc[i, result.columns.get_loc('current_return')] = (result.iloc[i]['close'] - entry_price) / entry_price
            
            # 패턴 체크
            # 3일 연속 양봉
            if i >= consecutive_up_days:
                consecutive_bullish = all(result.iloc[i-j]['is_bullish'] for j in range(consecutive_up_days))
                if consecutive_bullish:
                    # 강한 상승, 목표가 설정하여 계속 보유
                    if result.iloc[i]['current_return'] < 0.08:  # 8% 미달성
                        continue
                    else:
                        result.iloc[i, result.columns.get_loc('exit_signal')] = True
                        result.iloc[i, result.columns.get_loc('exit_reason')] = 'target_reached'
                        position_open = False
                        continue
            
            # 십자별 출현
            if result.iloc[i]['is_doji']:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'doji_pattern'
                position_open = False
                continue
            
            # 긴 위꼬리 음봉
            if result.iloc[i]['has_long_upper_shadow'] and not result.iloc[i]['is_bullish']:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'bearish_rejection'
                position_open = False
                continue
            
            # 기본 청산 조건
            if result.iloc[i]['current_return'] > 0.02 and result.iloc[i]['holding_days'] >= max_holding_days:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'profit_with_max_days'
                position_open = False
            elif result.iloc[i]['current_return'] < 0 and result.iloc[i]['holding_days'] >= 2:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'loss_cut'
                position_open = False
    
    return result


def composite_score_exit(df, entry_result, min_score=60, max_holding_days=10):
    """
    복합 점수 기반 전략
    """
    result = entry_result.copy()
    
    # VWAP 계산 (간단한 버전)
    result['vwap'] = (result['close'] * result.get('volume', 1)).cumsum() / result.get('volume', 1).cumsum()
    
    # 이동평균
    result['ma5'] = result['close'].rolling(window=5).mean()
    
    # RSI (이미 momentum_score_exit에서 계산한 방식 재사용)
    delta = result['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    result['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    result['ema12'] = result['close'].ewm(span=12).mean()
    result['ema26'] = result['close'].ewm(span=26).mean()
    result['macd'] = result['ema12'] - result['ema26']
    result['macd_signal'] = result['macd'].ewm(span=9).mean()
    
    # OBV (간단한 버전)
    if 'volume' in result.columns:
        result['obv'] = (np.sign(result['close'].diff()) * result['volume']).cumsum()
        result['obv_ma'] = result['obv'].rolling(window=20).mean()
    
    # 포지션 추적
    result['position'] = 0
    result['holding_days'] = 0
    result['exit_signal'] = False
    result['exit_reason'] = ''
    result['composite_score'] = 0
    
    position_open = False
    entry_price = 0
    
    for i in range(1, len(result)):
        # 복합 점수 계산
        score = 0
        
        # 가격 요소 (40점)
        if not pd.isna(entry_price) and position_open:
            if result.iloc[i]['close'] > entry_price:
                score += 20
        if not pd.isna(result.iloc[i]['ma5']):
            if result.iloc[i]['close'] > result.iloc[i]['ma5']:
                score += 10
        if not pd.isna(result.iloc[i]['vwap']):
            if result.iloc[i]['close'] > result.iloc[i]['vwap']:
                score += 10
        
        # 모멘텀 요소 (30점)
        if not pd.isna(result.iloc[i]['rsi']):
            if 50 < result.iloc[i]['rsi'] < 70:
                score += 15
        if not pd.isna(result.iloc[i]['macd']) and not pd.isna(result.iloc[i]['macd_signal']):
            if result.iloc[i]['macd'] > result.iloc[i]['macd_signal']:
                score += 15
        
        # 거래량 요소 (30점)
        if 'volume' in result.columns:
            vol_ma = result['volume'].rolling(window=20).mean()
            if not pd.isna(vol_ma.iloc[i]):
                if result.iloc[i]['volume'] > vol_ma.iloc[i] * 1.2:
                    score += 15
            if 'obv' in result.columns and not pd.isna(result.iloc[i]['obv']):
                if result.iloc[i]['obv'] > result.iloc[i-1]['obv']:
                    score += 15
        
        result.iloc[i, result.columns.get_loc('composite_score')] = score
        
        # 포지션 관리
        if result.iloc[i-1].get('buy_signal', result.iloc[i-1].get('entry_signal', False)) and not position_open:
            position_open = True
            entry_price = result.iloc[i].get('buy_price', result.iloc[i].get('entry_price', result.iloc[i]['open']))
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = 1
            
        elif position_open:
            result.iloc[i, result.columns.get_loc('position')] = 1
            result.iloc[i, result.columns.get_loc('holding_days')] = result.iloc[i-1]['holding_days'] + 1
            
            current_return = (result.iloc[i]['close'] - entry_price) / entry_price
            
            # 청산 조건
            if score < 40:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'low_score'
                position_open = False
            elif score >= 40 and score < 60 and current_return < 0:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'medium_score_loss'
                position_open = False
            elif result.iloc[i]['holding_days'] >= max_holding_days and score < 60:
                result.iloc[i, result.columns.get_loc('exit_signal')] = True
                result.iloc[i, result.columns.get_loc('exit_reason')] = 'max_days'
                position_open = False
    
    return result