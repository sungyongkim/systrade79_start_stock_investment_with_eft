# 개선된 calculate_momentum_portfolio_returns 함수 사용 예제

# momentum_portfolio_with_csv.py 에서 함수 import
from momentum_portfolio_with_csv import calculate_momentum_portfolio_returns, analyze_momentum_calculation, visualize_momentum_process

# 기존 노트북에서 사용하던 방식 그대로, CSV 저장 옵션만 추가
print("\n📊 상대모멘텀 포트폴리오 전략 분석 (CSV 저장 포함):")
print("=" * 80)

# CSV 저장을 포함한 상대모멘텀 계산
mom_daily, mom_cumulative, weights, momentum_df = calculate_momentum_portfolio_returns(
    stock_data,  # 이미 로드된 주가 데이터
    volatility_breakout_with_all_filters_v4,  # 전략 함수
    momentum_period=20,
    top_n=3,
    rebalance_period=30,
    k=0.3,
    adx_threshold=35,
    save_csv=True,  # CSV 저장 옵션 켜기
    csv_filename='momentum_analysis_TQQQ_SQQQ_ERX.csv'  # 원하는 파일명 지정
)

# 계산과정 분석
rebalance_summary, ticker_momentum = analyze_momentum_calculation(momentum_df)

# 시각화 (선택사항)
visualize_momentum_process(momentum_df, save_path='momentum_process_visualization.png')

# 성과 지표 계산
metrics = calculate_performance_metrics(mom_daily, mom_cumulative)
print(f"\n📊 상대모멘텀 전략 성과:")
print(f"총 수익률: {metrics['total_return']*100:.1f}%")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"MDD: {metrics['mdd']*100:.1f}%")
print(f"승률: {metrics['win_rate']*100:.1f}%")

# CSV 파일 내용 미리보기
print(f"\n📊 저장된 CSV 파일 미리보기 (처음 10행):")
print(momentum_df.head(10))

# 리밸런싱 시점별 상세 정보 출력
print(f"\n📊 최근 5회 리밸런싱 상세 정보:")
recent_rebalances = momentum_df['rebalance_date'].unique()[-5:]
for rebalance_date in recent_rebalances:
    print(f"\n리밸런싱 날짜: {rebalance_date}")
    rebalance_data = momentum_df[momentum_df['rebalance_date'] == rebalance_date]
    selected_data = rebalance_data[rebalance_data['selected']]
    
    print("선택된 종목:")
    for _, row in selected_data.iterrows():
        print(f"  - {row['ticker']}: 모멘텀 {row['momentum_score']:.2f}% (순위: {row['rank']})")
    
    print("선택되지 않은 종목:")
    not_selected = rebalance_data[~rebalance_data['selected']]
    for _, row in not_selected.iterrows():
        print(f"  - {row['ticker']}: 모멘텀 {row['momentum_score']:.2f}% (순위: {row['rank']})")