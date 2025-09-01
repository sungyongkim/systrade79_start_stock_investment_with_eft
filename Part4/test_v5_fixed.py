# v5 함수 테스트 (NA 에러 수정 버전)
import sys
sys.path.append('/Users/cg01-piwoo/FinvizBackTest_I/backtest/주식투자_ETF로_시작하라/Part4')

from volatility_breakout_with_all_filters_v5_fixed import volatility_breakout_with_all_filters_v5

# 노트북에서 이미 정의된 calculate_atr 함수가 필요합니다.
# 노트북에서 실행 시:
# from volatility_breakout_with_all_filters_v5_fixed import volatility_breakout_with_all_filters_v5

# v4(당일 지표) vs v5(전일 지표) 비교 테스트
print("\n📊 당일 지표 vs 전일 지표 기준 성과 비교:")
print("=" * 120)
print(f"{'티커':^10} | {'v4 (당일 지표)':^35} | {'v5 (전일 지표)':^35} | {'차이':^20}")
print(f"{'':^10} | {'수익률':^11}{'거래수':^10}{'승률':^10} | {'수익률':^11}{'거래수':^10}{'승률':^10} | {'수익률':^10}{'거래수':^10}")
print("-" * 120)

comparison_v4_v5 = {}

for ticker, df in stock_data.items():
    try:
        # v4 - 당일 지표 사용
        result_v4 = volatility_breakout_with_all_filters_v4(
            df, k=0.3, adx_threshold=35, 
            slippage=0.001, commission=0.0015
        )
        v4_return = (result_v4['cumulative_returns'].iloc[-1] - 1) * 100
        v4_trades = result_v4['buy_signal'].sum()
        v4_wins = (result_v4['returns'] > 0).sum()
        v4_win_rate = (v4_wins / v4_trades * 100) if v4_trades > 0 else 0
        
        # v5 - 전일 지표 사용 (수정된 버전)
        result_v5 = volatility_breakout_with_all_filters_v5(
            df, k=0.3, adx_threshold=35,
            slippage=0.001, commission=0.0015
        )
        v5_return = (result_v5['cumulative_returns'].iloc[-1] - 1) * 100
        v5_trades = result_v5['buy_signal'].sum()
        v5_wins = (result_v5['returns'] > 0).sum()
        v5_win_rate = (v5_wins / v5_trades * 100) if v5_trades > 0 else 0
        
        # 결과 저장
        comparison_v4_v5[ticker] = {
            'v4': {'return': v4_return, 'trades': v4_trades, 'win_rate': v4_win_rate},
            'v5': {'return': v5_return, 'trades': v5_trades, 'win_rate': v5_win_rate}
        }
        
        # 차이 계산
        return_diff = v5_return - v4_return
        trade_diff = v5_trades - v4_trades
        
        print(f"{ticker:^10} | {v4_return:^10.1f}%{v4_trades:^10}{v4_win_rate:^9.1f}% | "
              f"{v5_return:^10.1f}%{v5_trades:^10}{v5_win_rate:^9.1f}% | "
              f"{return_diff:^9.1f}%{trade_diff:^10}")
    except Exception as e:
        print(f"{ticker:^10} | 에러 발생: {str(e)}")

print("=" * 120)

# 평균 차이 계산
valid_results = [v for v in comparison_v4_v5.values() 
                 if not np.isnan(v['v5']['return']) and not np.isnan(v['v4']['return'])]
if valid_results:
    avg_return_diff = np.mean([v['v5']['return'] - v['v4']['return'] for v in valid_results])
    avg_trade_diff = np.mean([v['v5']['trades'] - v['v4']['trades'] for v in valid_results])
    
    print(f"\n💡 요약:")
    print(f"- 평균 수익률 차이: {avg_return_diff:.1f}%")
    print(f"- 평균 거래수 차이: {avg_trade_diff:.1f}회")
    print(f"\n⚠️  전일 지표 사용(v5)이 더 현실적이며 look-ahead bias를 방지합니다.")