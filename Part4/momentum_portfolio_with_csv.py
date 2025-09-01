import pandas as pd
import numpy as np
from datetime import datetime

def calculate_momentum_portfolio_returns(stock_data, strategy_func, momentum_period=20, 
                                       rebalance_period=30, top_n=3, save_csv=False, 
                                       csv_filename=None, calculate_today_signals=False, 
                                       calculate_intraday_signals=False, **kwargs):
    """
    상대모멘텀을 적용한 포트폴리오 수익률 계산
    
    Parameters:
    - stock_data: 종목 데이터 딕셔너리
    - strategy_func: 전략 함수
    - momentum_period: 모멘텀 계산 기간 (기본 20일)
    - rebalance_period: 리밸런싱 주기 (기본 30일)
    - top_n: 상위 n개 종목 선택 (기본 3개)
    - save_csv: CSV 파일 저장 여부 (기본 False)
    - csv_filename: 저장할 CSV 파일명 (기본값: momentum_calculation_YYYYMMDD_HHMMSS.csv)
    - calculate_today_signals: 오늘 날짜 기준 필터 계산 여부 (기본 False)
    - calculate_intraday_signals: 장중 필터 계산 여부 (기본 False)
    - **kwargs: 전략 함수에 전달할 추가 인자
    """
    # 모든 종목의 결과 저장
    all_results = {}
    all_dates = None
    
    # 각 종목별 전략 실행
    for ticker, df in stock_data.items():
        result = strategy_func(df, **kwargs)
        all_results[ticker] = result
        
        if all_dates is None:
            all_dates = set(result.index)
        else:
            all_dates = all_dates.intersection(set(result.index))
    
    # 공통 날짜만 선택
    common_dates = sorted(list(all_dates))
    
    # 포트폴리오 일일 수익률 저장
    portfolio_returns = pd.Series(index=common_dates, dtype=float)
    portfolio_returns[:] = 0.0
    
    # 종목별 가중치 기록
    weights_history = pd.DataFrame(index=common_dates, columns=list(stock_data.keys()))
    weights_history[:] = 0.0
    
    # 리밸런싱 날짜 계산
    rebalance_dates = common_dates[::rebalance_period]
    
    # 상대모멘텀 계산과정 저장을 위한 리스트
    momentum_calculation_records = []
    
    # 각 리밸런싱 기간별 처리
    for i in range(len(rebalance_dates)):
        start_date = rebalance_dates[i]
        end_date = rebalance_dates[i + 1] if i + 1 < len(rebalance_dates) else common_dates[-1]
        
        # 모멘텀 계산을 위한 과거 수익률
        momentum_start_idx = common_dates.index(start_date) - momentum_period
        if momentum_start_idx < 0:
            momentum_start_idx = 0
        
        # 각 종목의 모멘텀 스코어 계산
        momentum_scores = {}
        momentum_details = {}
        
        for ticker, result in all_results.items():
            # 모멘텀 기간 동안의 가격 데이터
            momentum_prices = result['close'].loc[common_dates[momentum_start_idx]:start_date]
            
            if len(momentum_prices) >= 2:
                # 시작가격과 종료가격
                start_price = momentum_prices.iloc[0]
                end_price = momentum_prices.iloc[-1]
                
                # 모멘텀 수익률 계산
                momentum_return = (end_price / start_price - 1) if start_price > 0 else 0
                
                # NaN이나 inf 처리
                if pd.isna(momentum_return) or np.isinf(momentum_return):
                    momentum_return = 0
                
                momentum_scores[ticker] = momentum_return
                momentum_details[ticker] = {
                    'start_price': start_price,
                    'end_price': end_price,
                    'momentum_return': momentum_return,
                    'momentum_period_start': momentum_prices.index[0],
                    'momentum_period_end': momentum_prices.index[-1]
                }
            else:
                momentum_scores[ticker] = 0
                momentum_details[ticker] = {
                    'start_price': 0,
                    'end_price': 0,
                    'momentum_return': 0,
                    'momentum_period_start': None,
                    'momentum_period_end': None
                }
        
        # 상위 N개 종목 선택
        sorted_tickers = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
        selected_tickers = [ticker for ticker, _ in sorted_tickers[:top_n]]
        
        # 선택된 종목에 동일 가중
        weight = 1.0 / len(selected_tickers) if selected_tickers else 0
        
        # 리밸런싱 시점의 계산과정 기록
        for rank, (ticker, score) in enumerate(sorted_tickers):
            record = {
                'rebalance_date': start_date,
                'ticker': ticker,
                'rank': rank + 1,
                'momentum_score': score * 100,  # 퍼센트로 변환
                'momentum_period_start': momentum_details[ticker]['momentum_period_start'],
                'momentum_period_end': momentum_details[ticker]['momentum_period_end'],
                'start_price': momentum_details[ticker]['start_price'],
                'end_price': momentum_details[ticker]['end_price'],
                'selected': ticker in selected_tickers,
                'weight': weight if ticker in selected_tickers else 0,
                'rebalance_period_start': start_date,
                'rebalance_period_end': end_date
            }
            momentum_calculation_records.append(record)
        
        # 해당 기간 동안의 수익률 계산
        period_dates = [d for d in common_dates if start_date <= d <= end_date]
        
        for date in period_dates:
            daily_return = 0.0
            
            # 선택된 종목들의 수익률 가중 평균
            for ticker in selected_tickers:
                ticker_return = all_results[ticker].loc[date, 'returns']
                # NaN이나 inf 처리
                if pd.isna(ticker_return) or np.isinf(ticker_return):
                    ticker_return = 0
                daily_return += ticker_return * weight
                weights_history.loc[date, ticker] = weight
            
            portfolio_returns.loc[date] = daily_return
    
    # 누적 수익률 계산 (NaN 처리)
    clean_returns = portfolio_returns.replace([np.inf, -np.inf], 0).fillna(0)
    portfolio_cumulative = (1 + clean_returns).cumprod()
    
    # 상대모멘텀 계산과정을 DataFrame으로 변환
    momentum_calculation_df = pd.DataFrame(momentum_calculation_records)
    
    # 오늘 날짜 기준 필터 계산 (선택사항)
    today_signals_df = None
    if calculate_today_signals and len(common_dates) > 0:
        today_date = common_dates[-1]  # 가장 최근 날짜를 오늘로 가정
        today_signals = []
        
        print(f"\n📊 오늘({today_date}) 기준 필터 계산:")
        print("=" * 80)
        
        # 다음 리밸런싱 날짜 계산
        days_since_last_rebalance = len(common_dates) % rebalance_period
        days_until_next_rebalance = rebalance_period - days_since_last_rebalance if days_since_last_rebalance > 0 else 0
        next_rebalance_date = common_dates[-1] if days_until_next_rebalance == 0 else None
        
        # 모멘텀 계산을 위한 시작 인덱스
        momentum_start_idx = max(0, len(common_dates) - momentum_period - 1)
        
        for ticker in stock_data.keys():
            if ticker in all_results:
                result = all_results[ticker]
                
                # 모멘텀 스코어 계산 (오늘 종가 기준)
                if momentum_start_idx < len(common_dates) - 1:
                    start_price = result['close'].iloc[momentum_start_idx]
                    current_price = result['close'].iloc[-1]
                    momentum_score = ((current_price - start_price) / start_price * 100) if start_price > 0 else 0
                else:
                    momentum_score = 0
                
                # 오늘의 필터 상태 확인 (전일 지표 기준)
                last_idx = result.index[-1]
                
                # 각 필터의 상태 확인
                uptrend = result.get('UPTREND', pd.Series(False)).loc[last_idx] if 'UPTREND' in result.columns else False
                green4 = result.get('GREEN4', pd.Series(False)).loc[last_idx] if 'GREEN4' in result.columns else False
                obv_filter = result.get('obv_filter', pd.Series(False)).loc[last_idx] if 'obv_filter' in result.columns else False
                green2 = result.get('GREEN2', pd.Series(False)).loc[last_idx] if 'GREEN2' in result.columns else False
                
                # 추가 지표 정보 (있는 경우)
                adx_value = result['adx_14'].iloc[-1] if 'adx_14' in result.columns else None
                obv_diff = (result['obv_values'].iloc[-1] - result['obv_9_ma'].iloc[-1]) if 'obv_values' in result.columns and 'obv_9_ma' in result.columns else None
                
                today_signal = {
                    'date': today_date,
                    'ticker': ticker,
                    'momentum_score': momentum_score,
                    'current_price': current_price,
                    'price_20d_ago': start_price,
                    'UPTREND': uptrend,
                    'GREEN4': green4,
                    'obv_filter': obv_filter,
                    'GREEN2': green2,
                    'any_filter_true': uptrend or green4 or obv_filter or green2,
                    'filter_count': sum([uptrend, green4, obv_filter, green2]),
                    'adx_14': adx_value,
                    'obv_diff': obv_diff,
                    'days_until_rebalance': days_until_next_rebalance,
                    'is_rebalance_day': days_until_next_rebalance == 0
                }
                
                today_signals.append(today_signal)
        
        # 오늘의 신호를 DataFrame으로 변환
        today_signals_df = pd.DataFrame(today_signals)
        today_signals_df = today_signals_df.sort_values('momentum_score', ascending=False)
        
        # 현재 포트폴리오에 포함될 종목 표시
        today_signals_df['would_be_selected'] = False
        today_signals_df.iloc[:top_n, today_signals_df.columns.get_loc('would_be_selected')] = True
        
        # 오늘의 신호 요약 출력
        print(f"\n📊 모멘텀 상위 {top_n}개 종목:")
        for idx, row in today_signals_df[today_signals_df['would_be_selected']].iterrows():
            filters = []
            if row['UPTREND']: filters.append('UPTREND')
            if row['GREEN4']: filters.append('GREEN4')
            if row['obv_filter']: filters.append('OBV')
            if row['GREEN2']: filters.append('GREEN2')
            
            print(f"{row['ticker']:>6}: 모멘텀 {row['momentum_score']:>6.2f}% | 필터: {', '.join(filters) if filters else 'None'}")
        
        print(f"\n📅 다음 리밸런싱까지: {days_until_next_rebalance}일")
        
        # CSV로 저장 (선택사항)
        if save_csv:
            today_filename = csv_filename.replace('.csv', '_today_signals.csv') if csv_filename else f'today_signals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            today_signals_df.to_csv(today_filename, index=False, encoding='utf-8-sig')
            print(f"📊 오늘의 신호가 '{today_filename}'에 저장되었습니다.")
    
    # CSV 저장 옵션이 켜져있으면 파일로 저장
    if save_csv:
        if csv_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"momentum_calculation_{timestamp}.csv"
        
        # 계산과정 CSV 저장
        momentum_calculation_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        print(f"\n📊 상대모멘텀 계산과정이 '{csv_filename}'에 저장되었습니다.")
        
        # 추가로 일별 포트폴리오 가중치도 저장
        weights_filename = csv_filename.replace('.csv', '_weights.csv')
        weights_history.to_csv(weights_filename, encoding='utf-8-sig')
        print(f"📊 일별 포트폴리오 가중치가 '{weights_filename}'에 저장되었습니다.")
        
        # 요약 통계 출력
        print(f"\n📊 상대모멘텀 계산 요약:")
        print(f"- 총 리밸런싱 횟수: {len(rebalance_dates)}회")
        print(f"- 총 계산 레코드: {len(momentum_calculation_df)}개")
        print(f"- 분석 기간: {common_dates[0]} ~ {common_dates[-1]}")
        print(f"- 평균 모멘텀 스코어: {momentum_calculation_df['momentum_score'].mean():.2f}%")
        
        # 종목별 선택 빈도
        selection_stats = momentum_calculation_df[momentum_calculation_df['selected']].groupby('ticker').size()
        print(f"\n📊 종목별 포트폴리오 편입 횟수:")
        for ticker, count in selection_stats.sort_values(ascending=False).items():
            print(f"  - {ticker}: {count}회")
        
        # CAGR 계산 및 출력
        total_days = len(common_dates)
        years = total_days / 252
        final_value = portfolio_cumulative.iloc[-1]
        cagr = (final_value ** (1/years) - 1) * 100 if years > 0 else 0
        
        print(f"\n📊 수익률 지표:")
        print(f"- 총 수익률: {(final_value - 1) * 100:.2f}%")
        print(f"- CAGR (연평균 복리 수익률): {cagr:.2f}%")
        print(f"- 투자 기간: {years:.2f}년 ({total_days}거래일)")
    
    # 장중 필터 계산 (선택사항)
    intraday_signals_df = None
    if calculate_intraday_signals and len(common_dates) > 0:
        # 어제 데이터를 기준으로 오늘 사용할 필터 계산
        intraday_signals = []
        yesterday_idx = -2 if len(common_dates) > 1 else -1  # 어제 인덱스
        
        print(f"\n📊 장중 사용 가능한 필터 상태 (어제 종가 기준):")
        print("=" * 80)
        
        for ticker in stock_data.keys():
            if ticker in all_results:
                result = all_results[ticker]
                
                # 어제까지의 데이터로 모멘텀 계산
                if len(result) > momentum_period:
                    # 어제 종가 기준 20일 모멘텀
                    yesterday_close = result['close'].iloc[yesterday_idx]
                    close_20d_ago = result['close'].iloc[yesterday_idx - momentum_period] if len(result) > momentum_period else yesterday_close
                    momentum_score = ((yesterday_close - close_20d_ago) / close_20d_ago * 100) if close_20d_ago > 0 else 0
                else:
                    momentum_score = 0
                
                # 어제 종가 시점의 필터 상태 (오늘 장중에 사용 가능)
                yesterday_data_idx = result.index[yesterday_idx]
                
                # 전일 지표 기준으로 계산된 필터들
                uptrend = result.get('UPTREND', pd.Series(False)).loc[yesterday_data_idx] if 'UPTREND' in result.columns else False
                green4 = result.get('GREEN4', pd.Series(False)).loc[yesterday_data_idx] if 'GREEN4' in result.columns else False
                obv_filter = result.get('obv_filter', pd.Series(False)).loc[yesterday_data_idx] if 'obv_filter' in result.columns else False
                green2 = result.get('GREEN2', pd.Series(False)).loc[yesterday_data_idx] if 'GREEN2' in result.columns else False
                
                # 어제의 지표 값들 (오늘 사용할 값)
                adx_value = result['adx_14'].iloc[yesterday_idx] if 'adx_14' in result.columns else None
                pdi_value = result['pdi_14'].iloc[yesterday_idx] if 'pdi_14' in result.columns else None
                mdi_value = result['mdi_14'].iloc[yesterday_idx] if 'mdi_14' in result.columns else None
                obv_value = result['obv_values'].iloc[yesterday_idx] if 'obv_values' in result.columns else None
                obv_ma = result['obv_9_ma'].iloc[yesterday_idx] if 'obv_9_ma' in result.columns else None
                
                # 오늘 사용할 목표가 계산을 위한 어제 Range
                yesterday_high = result['high'].iloc[yesterday_idx]
                yesterday_low = result['low'].iloc[yesterday_idx]
                yesterday_range = yesterday_high - yesterday_low
                
                intraday_signal = {
                    'ticker': ticker,
                    'momentum_score': momentum_score,
                    'yesterday_close': yesterday_close,
                    'yesterday_range': yesterday_range,
                    
                    # 오늘 장중에 확인 가능한 필터 상태
                    'UPTREND_active': uptrend,
                    'GREEN4_active': green4,
                    'obv_filter_active': obv_filter,
                    'GREEN2_active': green2,
                    'any_filter_active': uptrend or green4 or obv_filter or green2,
                    'active_filter_count': sum([uptrend, green4, obv_filter, green2]),
                    
                    # 지표 값들 (참고용)
                    'adx_14': adx_value,
                    'pdi_14': pdi_value,
                    'mdi_14': mdi_value,
                    'obv': obv_value,
                    'obv_ma': obv_ma,
                    'obv_diff': (obv_value - obv_ma) if obv_value and obv_ma else None,
                    
                    # 변동성 돌파 계산용
                    'target_multipliers': {
                        'k_0.3': yesterday_range * 0.3,
                        'k_0.5': yesterday_range * 0.5,
                        'k_0.7': yesterday_range * 0.7
                    }
                }
                
                intraday_signals.append(intraday_signal)
        
        # DataFrame으로 변환
        intraday_signals_df = pd.DataFrame(intraday_signals)
        intraday_signals_df = intraday_signals_df.sort_values('momentum_score', ascending=False)
        
        # 모멘텀 상위 종목 표시
        intraday_signals_df['momentum_rank'] = range(1, len(intraday_signals_df) + 1)
        intraday_signals_df['in_momentum_top_n'] = intraday_signals_df['momentum_rank'] <= top_n
        
        # 장중 모니터링 정보 출력
        print("\n📊 모멘텀 상위 종목 (어제 종가 기준):")
        print("-" * 80)
        print(f"{'순위':^6} {'티커':^8} {'모멘텀':^10} {'필터상태':^40} {'목표가(K=0.5)':^15}")
        print("-" * 80)
        
        for _, row in intraday_signals_df.head(top_n).iterrows():
            filters = []
            if row['UPTREND_active']: filters.append('ADX↑')
            if row['GREEN4_active']: filters.append('Chaikin↑')
            if row['obv_filter_active']: filters.append('OBV↑')
            if row['GREEN2_active']: filters.append('GREEN2')
            filter_str = ', '.join(filters) if filters else '필터 없음'
            
            # 목표가 = 오늘 시가 + 어제 Range * K
            target_addon = row['target_multipliers']['k_0.5']
            
            print(f"{row['momentum_rank']:^6} {row['ticker']:^8} {row['momentum_score']:^9.1f}% "
                  f"{filter_str:^40} 시가+{target_addon:>6.2f}")
        
        print("\n📌 장중 사용 방법:")
        print("1. 오늘 시가 확인 후 각 종목의 목표가 계산 (시가 + 표시된 값)")
        print("2. 장중에 목표가 돌파 시 해당 종목이 필터 조건을 만족하는지 확인")
        print("3. 모멘텀 순위와 필터 상태를 모두 고려하여 매수 결정")
        
        # CSV 저장 (선택사항)
        if save_csv:
            intraday_filename = csv_filename.replace('.csv', '_intraday_signals.csv') if csv_filename else f'intraday_signals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            intraday_signals_df.to_csv(intraday_filename, index=False, encoding='utf-8-sig')
            print(f"\n📊 장중 신호가 '{intraday_filename}'에 저장되었습니다.")
    
    # CAGR 계산
    total_days = len(common_dates)
    years = total_days / 252  # 거래일 기준
    final_value = portfolio_cumulative.iloc[-1]
    cagr = (final_value ** (1/years) - 1) * 100 if years > 0 else 0
    
    # 성과 지표 딕셔너리 생성
    performance_metrics = {
        'total_return': (final_value - 1) * 100,
        'cagr': cagr,
        'total_days': total_days,
        'years': years,
        'final_value': final_value
    }
    
    # 모든 결과 반환
    return portfolio_returns, portfolio_cumulative, weights_history, momentum_calculation_df, today_signals_df, intraday_signals_df, performance_metrics


# 사용 예시를 위한 헬퍼 함수
def analyze_momentum_calculation(momentum_df):
    """
    상대모멘텀 계산 DataFrame을 분석하여 통계 정보 출력
    """
    print("\n📊 상대모멘텀 계산과정 분석:")
    print("=" * 80)
    
    # 리밸런싱 날짜별 요약
    rebalance_summary = momentum_df.groupby('rebalance_date').agg({
        'ticker': 'count',
        'momentum_score': ['mean', 'std', 'min', 'max'],
        'selected': 'sum'
    })
    
    print("\n리밸런싱 날짜별 요약:")
    print(rebalance_summary.tail(10))
    
    # 종목별 평균 모멘텀 스코어
    ticker_momentum = momentum_df.groupby('ticker')['momentum_score'].agg(['mean', 'std', 'count'])
    ticker_momentum = ticker_momentum.sort_values('mean', ascending=False)
    
    print("\n\n종목별 평균 모멘텀 스코어:")
    print(ticker_momentum)
    
    # 선택된 종목의 평균 모멘텀 vs 선택되지 않은 종목
    selected_momentum = momentum_df[momentum_df['selected']]['momentum_score'].mean()
    not_selected_momentum = momentum_df[~momentum_df['selected']]['momentum_score'].mean()
    
    print(f"\n\n선택된 종목의 평균 모멘텀: {selected_momentum:.2f}%")
    print(f"선택되지 않은 종목의 평균 모멘텀: {not_selected_momentum:.2f}%")
    print(f"차이: {selected_momentum - not_selected_momentum:.2f}%p")
    
    return rebalance_summary, ticker_momentum


# 시각화 함수 추가
def visualize_momentum_process(momentum_df, save_path=None):
    """
    상대모멘텀 계산과정을 시각화
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 1. 리밸런싱별 모멘텀 스코어 분포
    ax1 = axes[0, 0]
    rebalance_dates = momentum_df['rebalance_date'].unique()[-12:]  # 최근 12번
    for date in rebalance_dates:
        date_data = momentum_df[momentum_df['rebalance_date'] == date]
        ax1.bar(date_data['ticker'], date_data['momentum_score'], 
                alpha=0.6, label=str(date)[:7])
    ax1.set_title('최근 12회 리밸런싱 시 모멘텀 스코어')
    ax1.set_xlabel('종목')
    ax1.set_ylabel('모멘텀 스코어 (%)')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    
    # 2. 종목별 선택 빈도
    ax2 = axes[0, 1]
    selection_counts = momentum_df[momentum_df['selected']].groupby('ticker').size()
    selection_counts.plot(kind='bar', ax=ax2, color='skyblue')
    ax2.set_title('종목별 포트폴리오 편입 횟수')
    ax2.set_xlabel('종목')
    ax2.set_ylabel('선택 횟수')
    
    # 3. 시간에 따른 평균 모멘텀 변화
    ax3 = axes[1, 0]
    momentum_by_date = momentum_df.groupby('rebalance_date')['momentum_score'].mean()
    ax3.plot(momentum_by_date.index, momentum_by_date.values, marker='o')
    ax3.set_title('시간에 따른 평균 모멘텀 스코어 변화')
    ax3.set_xlabel('날짜')
    ax3.set_ylabel('평균 모멘텀 스코어 (%)')
    ax3.grid(True, alpha=0.3)
    
    # 4. 선택 vs 비선택 종목의 모멘텀 분포
    ax4 = axes[1, 1]
    selected_data = momentum_df[momentum_df['selected']]['momentum_score']
    not_selected_data = momentum_df[~momentum_df['selected']]['momentum_score']
    
    ax4.hist([selected_data, not_selected_data], bins=30, 
             label=['선택됨', '선택안됨'], alpha=0.7, color=['green', 'red'])
    ax4.set_title('선택/비선택 종목의 모멘텀 스코어 분포')
    ax4.set_xlabel('모멘텀 스코어 (%)')
    ax4.set_ylabel('빈도')
    ax4.legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 시각화 차트가 '{save_path}'에 저장되었습니다.")
    
    plt.show()