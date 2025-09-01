# 오늘 날짜 기준 필터 계산 테스트
from momentum_portfolio_with_csv import calculate_momentum_portfolio_returns

# 노트북에서 실행할 때 사용할 수 있는 예제 코드
print("\n📊 오늘 기준 상대모멘텀 및 필터 계산 테스트:")
print("=" * 80)

# calculate_today_signals=True로 설정하여 오늘의 신호 계산
mom_daily, mom_cumulative, weights, momentum_df, today_signals = calculate_momentum_portfolio_returns(
    stock_data,  # 이미 로드된 주가 데이터
    volatility_breakout_with_all_filters_v4,  # 전략 함수
    momentum_period=20,
    top_n=3,
    rebalance_period=30,
    k=0.3,
    adx_threshold=35,
    save_csv=True,
    csv_filename='momentum_with_today_signals.csv',
    calculate_today_signals=True  # 오늘 신호 계산 켜기
)

# 오늘의 신호 분석
if today_signals is not None:
    print("\n📊 오늘의 전체 종목 상태:")
    print(today_signals[['ticker', 'momentum_score', 'UPTREND', 'GREEN4', 'obv_filter', 'GREEN2', 'filter_count', 'would_be_selected']])
    
    # 필터가 활성화된 종목만 보기
    active_filters = today_signals[today_signals['any_filter_true']]
    print(f"\n📊 필터가 활성화된 종목: {len(active_filters)}개")
    print(active_filters[['ticker', 'momentum_score', 'filter_count']].to_string())
    
    # 리밸런싱 날인 경우
    if today_signals.iloc[0]['is_rebalance_day']:
        print("\n🔄 오늘은 리밸런싱 날입니다!")
        selected = today_signals[today_signals['would_be_selected']]
        print("선택된 종목:")
        for _, row in selected.iterrows():
            print(f"  - {row['ticker']}: 모멘텀 {row['momentum_score']:.2f}%")
    else:
        days_left = today_signals.iloc[0]['days_until_rebalance']
        print(f"\n📅 다음 리밸런싱까지 {days_left}일 남았습니다.")
        
        # 현재 포트폴리오와 비교
        current_portfolio_tickers = weights.columns[weights.iloc[-1] > 0].tolist()
        print(f"\n현재 포트폴리오: {', '.join(current_portfolio_tickers)}")
        
        # 만약 오늘 리밸런싱한다면 선택될 종목
        would_be_selected = today_signals[today_signals['would_be_selected']]['ticker'].tolist()
        print(f"오늘 리밸런싱 시 선택될 종목: {', '.join(would_be_selected)}")
        
        # 변경사항
        removed = set(current_portfolio_tickers) - set(would_be_selected)
        added = set(would_be_selected) - set(current_portfolio_tickers)
        if removed or added:
            print("\n변경 예상:")
            if removed:
                print(f"  제외될 종목: {', '.join(removed)}")
            if added:
                print(f"  추가될 종목: {', '.join(added)}")

# 실시간 모니터링을 위한 함수
def monitor_today_signals(stock_data, strategy_func, **kwargs):
    """매일 실행하여 현재 상태를 모니터링하는 함수"""
    _, _, _, _, today_signals = calculate_momentum_portfolio_returns(
        stock_data,
        strategy_func,
        calculate_today_signals=True,
        save_csv=False,  # 모니터링 시에는 CSV 저장 안함
        **kwargs
    )
    
    if today_signals is not None:
        # 간단한 대시보드 형태로 출력
        print("\n" + "="*60)
        print(f"{'📊 Daily Momentum & Filter Monitor':^60}")
        print("="*60)
        print(f"Date: {today_signals.iloc[0]['date']}")
        print(f"Days until rebalance: {today_signals.iloc[0]['days_until_rebalance']}")
        print("\nTop 5 Momentum Stocks:")
        print("-"*60)
        print(f"{'Rank':^6} {'Ticker':^8} {'Momentum':^10} {'Filters':^30}")
        print("-"*60)
        
        for i, row in today_signals.head(5).iterrows():
            filters = []
            if row['UPTREND']: filters.append('ADX↑')
            if row['GREEN4']: filters.append('Chaikin↑')
            if row['obv_filter']: filters.append('OBV↑')
            if row['GREEN2']: filters.append('GREEN2')
            filter_str = ', '.join(filters) if filters else '-'
            
            rank = i + 1
            selected = '★' if row['would_be_selected'] else ' '
            print(f"{rank:^6} {row['ticker']:^8} {row['momentum_score']:^9.1f}% {filter_str:^30} {selected}")
        
        print("="*60)
    
    return today_signals

# 사용 예시
# today_status = monitor_today_signals(stock_data, volatility_breakout_with_all_filters_v4, 
#                                      k=0.3, adx_threshold=35)