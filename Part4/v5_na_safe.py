# v5 함수의 NA 안전 버전
def volatility_breakout_with_all_filters_v5_safe(df, k=0.5, adx_threshold=20, 
                                        momentum_threshold=0.0, momentum_period=20, use_atr_filter=True, atr_period=20,
                                        slippage=0.0, commission=0.0):
    """
    변동성 돌파 + ADX/Chaikin + 절대모멘텀 + ATR 필터를 모두 적용한 전략
    (전일 기준 지표 사용 버전 - NA 안전 처리)
    """
    result = df.copy()
    
    # ========== 당일 기준 계산 (변동성 돌파용) ==========
    # 전일 Range 계산
    result['prev_range'] = (result['high'] - result['low']).shift(1)
    
    # 진입가 계산 (당일 시가 + 전일 Range × K)
    result['target_price'] = result['open'] + (result['prev_range'] * k)
    
    # 변동성 돌파 신호 (당일 고가로 확인)
    result['volatility_signal'] = result['high'] > result['target_price']
    
    # ========== 전일 기준 지표들 ==========
    # ADX 관련 지표를 전일 값으로 shift
    result['adx_14_prev'] = result['adx_14'].shift(1)
    result['pdi_14_prev'] = result['pdi_14'].shift(1)
    result['mdi_14_prev'] = result['mdi_14'].shift(1)
    
    # ADX 필터 조건 (전일 ADX > threshold & 전일 +DI > 전일 -DI)
    result['UPTREND'] = (
        (result['adx_14_prev'] > adx_threshold) & 
        (result['pdi_14_prev'] > result['mdi_14_prev'])
    )
    
    # OBV 관련 지표들을 전일 값으로 shift
    result['obv_values_prev'] = result['obv_values'].shift(1)
    result['obv_9_ma_prev'] = result['obv_9_ma'].shift(1)
    result['obv_yesterday'] = result['obv_values'].shift(2)  # 전전일 OBV
    
    # OBV 필터 조건 (전일 ADX < threshold & 전일 OBV > 전전일 OBV)
    result['obv_filter'] = (
        (result['adx_14_prev'] < adx_threshold) & 
        (result['obv_values_prev'] > result['obv_yesterday'])
    )
    
    # Chaikin 관련 지표들을 전일 값으로 shift
    result['chaikin_oscillator_prev'] = result['chaikin_oscillator'].shift(1)
    result['chaikin_signal_prev'] = result['chaikin_signal'].shift(1)
    result['chaikin_yesterday'] = result['chaikin_oscillator'].shift(2)  # 전전일 Chaikin
    
    # GREEN4 : Chaikin 필터 조건 (전일 ADX > threshold & 전일 Chaikin > 전전일 Chaikin)
    result['GREEN4'] = (
        (result['adx_14_prev'] > adx_threshold) & 
        (result['chaikin_oscillator_prev'] > result['chaikin_yesterday'])
    )
    
    # 절대 모멘텀 계산 (전일 종가 기준 20일 수익률)
    result['close_prev'] = result['close'].shift(1)
    result['close_20days_ago'] = result['close'].shift(momentum_period + 1)
    # 0으로 나누기 방지
    result['momentum_20'] = 0.0
    mask = result['close_20days_ago'] > 0
    result.loc[mask, 'momentum_20'] = (
        (result.loc[mask, 'close_prev'] - result.loc[mask, 'close_20days_ago']) / 
        result.loc[mask, 'close_20days_ago']
    )
    result['momentum_filter'] = result['momentum_20'] > momentum_threshold
    
    # ATR 계산 (전일 기준)
    result['atr'] = calculate_atr(result, atr_period)
    result['atr_prev'] = result['atr'].shift(1)
    result['atr_ma_prev'] = result['atr'].shift(1).rolling(window=atr_period).mean()
    
    # GREEN2 : UPTREND & OBV DIFF > 0 (전일 기준)
    result['GREEN2'] = (
        (result['adx_14_prev'] > adx_threshold) & 
        (result['pdi_14_prev'] > result['mdi_14_prev']) &
        ((result['obv_values_prev'] - result['obv_9_ma_prev']) > 0)
    )
    
    if use_atr_filter:
        result['atr_filter'] = result['atr_prev'] > result['atr_ma_prev']
    else:
        result['atr_filter'] = True  # ATR 필터 미사용 시 항상 True
    
    # MACD 관련 (있는 경우에만)
    if 'macd_signals' in df.columns:
        result['macd_signals_prev'] = result['macd_signals'].shift(1)
        result['macd_filter'] = result['macd_signals_prev'] == 'BUY'
    else:
        result['macd_filter'] = False
    
    # 최종 매수 신호 (변동성 돌파는 당일, 나머지 필터는 전일 기준)
    # NA 값을 fillna로 처리
    result['obv_filter'] = result['obv_filter'].fillna(False)
    result['GREEN2'] = result['GREEN2'].fillna(False)
    result['GREEN4'] = result['GREEN4'].fillna(False)
    result['macd_filter'] = result['macd_filter'].fillna(False)
    
    result['buy_signal'] = (
        result['volatility_signal'] &  # 당일 변동성 돌파
        (result['obv_filter'] | result['GREEN2'] | result['GREEN4'] | result['macd_filter'])  # 전일 기준 필터
    )
    
    # 매수가와 매도가 (슬리피지 적용)
    result['buy_price'] = result['target_price'] * (1 + slippage)
    result['sell_price'] = result['open'].shift(-1) * (1 - slippage) if slippage > 0 else result['open'].shift(-1)
    
    # 수익률 계산 (수수료 포함)
    result['returns'] = 0.0
    buy_condition = result['buy_signal'] == True
    
    if commission > 0:
        # 수수료를 고려한 수익률
        result.loc[buy_condition, 'returns'] = (
            (result.loc[buy_condition, 'sell_price'] - result.loc[buy_condition, 'buy_price']) / 
            result.loc[buy_condition, 'buy_price'] - (2 * commission)
        )
    else:
        # 수수료 없는 수익률
        result.loc[buy_condition, 'returns'] = (
            (result.loc[buy_condition, 'sell_price'] - result.loc[buy_condition, 'buy_price']) / 
            result.loc[buy_condition, 'buy_price']
        )
    
    # 누적 수익률 계산
    result['cumulative_returns'] = (1 + result['returns']).cumprod()
    
    # Buy & Hold 수익률
    result['buy_hold_returns'] = result['close'] / result['close'].iloc[0]
    
    # 어떤 필터로 진입했는지 표시
    result['entry_type'] = 'none'
    
    # NA 안전하게 entry_type 설정
    result['UPTREND'] = result['UPTREND'].fillna(False)
    
    result.loc[result['buy_signal'] & result['UPTREND'], 'entry_type'] = 'ADX'
    result.loc[result['buy_signal'] & result['GREEN4'], 'entry_type'] = 'Chaikin'
    result.loc[result['buy_signal'] & result['obv_filter'], 'entry_type'] = 'OBV'
    result.loc[result['buy_signal'] & result['GREEN2'], 'entry_type'] = 'GREEN2'
    
    if 'macd_signals' in df.columns:
        result.loc[result['buy_signal'] & result['macd_filter'], 'entry_type'] = 'MACD'
    
    # 복수 조건 충족 시 (NA 안전 처리)
    uptrend_count = result['UPTREND'].fillna(False).astype(int)
    green4_count = result['GREEN4'].fillna(False).astype(int)
    obv_filter_count = result['obv_filter'].fillna(False).astype(int)
    green2_count = result['GREEN2'].fillna(False).astype(int)
    macd_filter_count = result['macd_filter'].fillna(False).astype(int) if 'macd_signals' in df.columns else 0
    
    total_count = uptrend_count + green4_count + obv_filter_count + green2_count + macd_filter_count
    
    multiple_conditions = (result['buy_signal'] == True) & (total_count > 1)
    result.loc[multiple_conditions, 'entry_type'] = 'Multiple'
    
    return result