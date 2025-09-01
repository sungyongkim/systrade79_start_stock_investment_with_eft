# 장중 필터 계산 테스트
from momentum_portfolio_with_csv import calculate_momentum_portfolio_returns

# 노트북에서 실행할 때 사용할 수 있는 예제 코드
print("\n📊 장중 매매를 위한 필터 상태 계산:")
print("=" * 80)

# calculate_intraday_signals=True로 설정하여 장중 신호 계산
results = calculate_momentum_portfolio_returns(
    stock_data,  # 이미 로드된 주가 데이터
    volatility_breakout_with_all_filters_v4,  # 전략 함수 (또는 v5)
    momentum_period=20,
    top_n=3,
    rebalance_period=30,
    k=0.3,
    adx_threshold=35,
    save_csv=True,
    csv_filename='momentum_with_intraday_signals.csv',
    calculate_today_signals=True,  # 오늘 신호도 계산
    calculate_intraday_signals=True  # 장중 신호 계산 켜기
)

# 결과 언패킹
mom_daily, mom_cumulative, weights, momentum_df, today_signals, intraday_signals = results

# 장중 신호 상세 분석
if intraday_signals is not None:
    print("\n📊 장중 매매 신호 상세:")
    print("=" * 80)
    
    # 필터가 활성화된 종목만 보기
    active_filter_stocks = intraday_signals[intraday_signals['any_filter_active']]
    print(f"\n✅ 필터 조건을 만족하는 종목: {len(active_filter_stocks)}개")
    
    for _, row in active_filter_stocks.iterrows():
        print(f"\n{row['ticker']}:")
        print(f"  - 모멘텀 순위: {row['momentum_rank']}위 ({row['momentum_score']:.2f}%)")
        print(f"  - 어제 종가: ${row['yesterday_close']:.2f}")
        print(f"  - 어제 변동폭: ${row['yesterday_range']:.2f}")
        print(f"  - 활성 필터: ", end="")
        
        filters = []
        if row['UPTREND_active']: filters.append('ADX↑')
        if row['GREEN4_active']: filters.append('Chaikin↑')
        if row['obv_filter_active']: filters.append('OBV↑')
        if row['GREEN2_active']: filters.append('GREEN2')
        print(', '.join(filters))
        
        print(f"  - 목표가 계산:")
        for k, addon in row['target_multipliers'].items():
            print(f"    • {k}: 오늘 시가 + ${addon:.2f}")
    
    # 실전 매매 가이드
    print("\n📝 오늘의 실전 매매 가이드:")
    print("=" * 80)
    
    # 모멘텀 상위 + 필터 만족 종목
    trade_candidates = intraday_signals[
        (intraday_signals['in_momentum_top_n']) & 
        (intraday_signals['any_filter_active'])
    ]
    
    if len(trade_candidates) > 0:
        print("매매 후보 종목:")
        for _, row in trade_candidates.iterrows():
            filters = []
            if row['UPTREND_active']: filters.append('ADX')
            if row['GREEN4_active']: filters.append('Chaikin')
            if row['obv_filter_active']: filters.append('OBV')
            if row['GREEN2_active']: filters.append('GREEN2')
            
            print(f"\n🎯 {row['ticker']}:")
            print(f"   - 모멘텀: {row['momentum_score']:.2f}% (순위: {row['momentum_rank']})")
            print(f"   - 필터: {', '.join(filters)}")
            print(f"   - 목표가(K=0.3): 시가 + ${row['target_multipliers']['k_0.3']:.2f}")
            print(f"   - 목표가(K=0.5): 시가 + ${row['target_multipliers']['k_0.5']:.2f}")
            print(f"   - ADX: {row['adx_14']:.1f}" if row['adx_14'] else "   - ADX: N/A")
    else:
        print("⚠️  모멘텀 상위 종목 중 필터 조건을 만족하는 종목이 없습니다.")
    
    # 대시보드 스타일 요약
    print("\n📊 장중 모니터링 대시보드:")
    print("=" * 80)
    print(intraday_signals[['ticker', 'momentum_rank', 'momentum_score', 
                           'UPTREND_active', 'GREEN4_active', 'obv_filter_active', 
                           'GREEN2_active', 'active_filter_count']].head(10).to_string(index=False))


# 실시간 장중 체크리스트 함수
def generate_intraday_checklist(intraday_signals_df, k_value=0.5):
    """장중 매매를 위한 체크리스트 생성"""
    
    print("\n" + "="*60)
    print(f"{'📋 장중 매매 체크리스트':^60}")
    print("="*60)
    print(f"설정: K={k_value}")
    print("-"*60)
    
    candidates = intraday_signals_df[intraday_signals_df['any_filter_active']].head(5)
    
    for _, row in candidates.iterrows():
        print(f"\n[ ] {row['ticker']} (모멘텀 {row['momentum_score']:.1f}%)")
        target_addon = row['target_multipliers'][f'k_{k_value}']
        print(f"    목표가: 시가 + ${target_addon:.2f}")
        print(f"    필터: ", end="")
        
        filters = []
        if row['UPTREND_active']: filters.append('✓ADX')
        if row['GREEN4_active']: filters.append('✓Chaikin')
        if row['obv_filter_active']: filters.append('✓OBV')
        if row['GREEN2_active']: filters.append('✓GREEN2')
        print(' '.join(filters))
        
        print(f"    체크: 시가[    ] → 목표가[    ] → 매수가[    ]")
    
    print("\n" + "="*60)
    print("💡 사용법: 장 시작 시 시가를 입력하고 목표가 계산")
    print("="*60)
    
    return candidates

# 체크리스트 생성 예시
if intraday_signals is not None:
    checklist = generate_intraday_checklist(intraday_signals, k_value=0.3)