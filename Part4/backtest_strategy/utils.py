"""
백테스트 유틸리티 함수들
성과 측정, 포트폴리오 계산, 시각화 등
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
from datetime import datetime


def calculate_performance_metrics(returns_series, risk_free_rate=0.02):
    """
    전략의 성과 지표 계산
    
    Parameters:
    - returns_series: 일별 수익률 시리즈
    - risk_free_rate: 무위험 수익률 (연율, 기본 2%)
    
    Returns:
    - dict: 성과 지표들
    """
    # 기본 통계
    total_return = (1 + returns_series).prod() - 1
    annual_return = (1 + total_return) ** (252 / len(returns_series)) - 1
    
    # 변동성
    daily_volatility = returns_series.std()
    annual_volatility = daily_volatility * np.sqrt(252)
    
    # 샤프 비율
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
    
    # 최대 낙폭 (MDD)
    cumulative = (1 + returns_series).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # 승률
    win_rate = (returns_series > 0).sum() / len(returns_series[returns_series != 0]) if len(returns_series[returns_series != 0]) > 0 else 0
    
    # 평균 손익
    winning_trades = returns_series[returns_series > 0]
    losing_trades = returns_series[returns_series < 0]
    
    avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0
    
    # 손익비
    profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
    
    # Calmar Ratio
    calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # 거래 횟수
    num_trades = len(returns_series[returns_series != 0])
    
    return {
        '누적수익률': f"{total_return:.2%}",
        '연환산수익률': f"{annual_return:.2%}",
        '연환산변동성': f"{annual_volatility:.2%}",
        '샤프비율': f"{sharpe_ratio:.2f}",
        '최대낙폭': f"{max_drawdown:.2%}",
        '승률': f"{win_rate:.2%}",
        '평균수익': f"{avg_win:.2%}",
        '평균손실': f"{avg_loss:.2%}",
        '손익비': f"{profit_loss_ratio:.2f}",
        'Calmar비율': f"{calmar_ratio:.2f}",
        '거래횟수': num_trades,
        '일평균거래': f"{num_trades/len(returns_series):.1f}"
    }


def calculate_portfolio_returns(strategy_results_dict, weights=None):
    """
    여러 전략의 포트폴리오 수익률 계산
    
    Parameters:
    - strategy_results_dict: {전략명: DataFrame} 딕셔너리
    - weights: 각 전략의 가중치 리스트 (None이면 동일 가중)
    
    Returns:
    - DataFrame: 포트폴리오 결과
    """
    strategies = list(strategy_results_dict.keys())
    
    if weights is None:
        weights = [1/len(strategies)] * len(strategies)
    
    # 날짜를 인덱스로 정렬
    aligned_returns = pd.DataFrame()
    
    for strategy, result_df in strategy_results_dict.items():
        if 'returns' in result_df.columns:
            aligned_returns[strategy] = result_df['returns']
    
    # 포트폴리오 수익률 계산
    portfolio_returns = (aligned_returns * weights).sum(axis=1)
    
    # 개별 전략 누적 수익률
    cumulative_returns = pd.DataFrame()
    for strategy in strategies:
        cumulative_returns[strategy] = (1 + aligned_returns[strategy]).cumprod()
    
    # 포트폴리오 누적 수익률
    cumulative_returns['Portfolio'] = (1 + portfolio_returns).cumprod()
    
    return {
        'returns': portfolio_returns,
        'cumulative_returns': cumulative_returns,
        'weights': dict(zip(strategies, weights))
    }


def plot_strategy_comparison(strategy_results_dict, metrics_to_plot=['cumulative_returns', 'drawdown'], 
                           figsize=(15, 10)):
    """
    여러 전략의 성과 비교 시각화
    
    Parameters:
    - strategy_results_dict: {전략명: DataFrame} 딕셔너리
    - metrics_to_plot: 시각화할 지표 리스트
    - figsize: 그래프 크기
    
    Returns:
    - fig: matplotlib figure 객체
    """
    num_plots = len(metrics_to_plot)
    fig, axes = plt.subplots(num_plots, 1, figsize=figsize, sharex=True)
    
    if num_plots == 1:
        axes = [axes]
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(strategy_results_dict)))
    
    for idx, metric in enumerate(metrics_to_plot):
        ax = axes[idx]
        
        if metric == 'cumulative_returns':
            for (strategy, result_df), color in zip(strategy_results_dict.items(), colors):
                if 'cumulative_returns' in result_df.columns:
                    ax.plot(result_df.index, result_df['cumulative_returns'], 
                           label=strategy, color=color, linewidth=2)
            
            ax.set_ylabel('누적 수익률')
            ax.set_title('전략별 누적 수익률 비교')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            
        elif metric == 'drawdown':
            for (strategy, result_df), color in zip(strategy_results_dict.items(), colors):
                if 'cumulative_returns' in result_df.columns:
                    cumulative = result_df['cumulative_returns']
                    running_max = cumulative.expanding().max()
                    drawdown = (cumulative - running_max) / running_max
                    
                    ax.fill_between(result_df.index, drawdown * 100, 0, 
                                   alpha=0.3, color=color, label=strategy)
            
            ax.set_ylabel('낙폭 (%)')
            ax.set_title('전략별 낙폭 (Drawdown) 비교')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            
        elif metric == 'returns_distribution':
            returns_data = []
            labels = []
            
            for strategy, result_df in strategy_results_dict.items():
                if 'returns' in result_df.columns:
                    non_zero_returns = result_df['returns'][result_df['returns'] != 0]
                    returns_data.append(non_zero_returns * 100)
                    labels.append(strategy)
            
            ax.boxplot(returns_data, labels=labels)
            ax.set_ylabel('수익률 (%)')
            ax.set_title('전략별 수익률 분포')
            ax.grid(True, alpha=0.3, axis='y')
            
        elif metric == 'monthly_returns':
            for strategy, result_df in strategy_results_dict.items():
                if 'returns' in result_df.columns:
                    # 월별 수익률 계산
                    result_df['year_month'] = pd.to_datetime(result_df.index).to_period('M')
                    monthly_returns = result_df.groupby('year_month')['returns'].apply(
                        lambda x: (1 + x).prod() - 1
                    )
                    
                    # 히트맵 데이터 준비
                    pivot_table = monthly_returns.reset_index()
                    pivot_table['year'] = pivot_table['year_month'].dt.year
                    pivot_table['month'] = pivot_table['year_month'].dt.month
                    pivot_table = pivot_table.pivot(index='year', columns='month', values='returns')
                    
                    # 서브플롯 생성
                    if HAS_SEABORN:
                        sns.heatmap(pivot_table * 100, annot=True, fmt='.1f', 
                                   cmap='RdYlGn', center=0, ax=ax,
                                   cbar_kws={'label': '수익률 (%)'})
                    ax.set_title(f'{strategy} - 월별 수익률 히트맵')
                    break  # 첫 번째 전략만 표시 (여러 개는 별도 figure 필요)
    
    # 마지막 서브플롯에 x축 레이블 추가
    if 'date' in result_df.columns:
        axes[-1].set_xlabel('날짜')
    else:
        axes[-1].set_xlabel('기간')
    
    plt.tight_layout()
    
    # 성과 지표 테이블 추가
    metrics_data = []
    for strategy, result_df in strategy_results_dict.items():
        if 'returns' in result_df.columns:
            metrics = calculate_performance_metrics(result_df['returns'])
            metrics['전략'] = strategy
            metrics_data.append(metrics)
    
    if metrics_data:
        metrics_df = pd.DataFrame(metrics_data)
        metrics_df = metrics_df.set_index('전략')
        
        # 테이블을 별도 figure로 생성
        fig_table = plt.figure(figsize=(12, len(metrics_data) * 0.5 + 1))
        ax_table = fig_table.add_subplot(111)
        ax_table.axis('tight')
        ax_table.axis('off')
        
        table = ax_table.table(cellText=metrics_df.values,
                              colLabels=metrics_df.columns,
                              rowLabels=metrics_df.index,
                              cellLoc='center',
                              loc='center')
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        
        # 헤더 스타일
        for i in range(len(metrics_df.columns)):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # 인덱스 스타일
        for i in range(1, len(metrics_df) + 1):
            table[(i, -1)].set_facecolor('#f0f0f0')
            table[(i, -1)].set_text_props(weight='bold')
        
        plt.title('전략별 성과 지표 비교', fontsize=14, fontweight='bold', pad=20)
    
    return fig


def analyze_exit_reasons(result_df):
    """
    청산 사유 분석
    
    Parameters:
    - result_df: exit_reason 컬럼이 있는 결과 DataFrame
    
    Returns:
    - dict: 청산 사유별 통계
    """
    if 'exit_reason' not in result_df.columns:
        return None
    
    # 청산 사유별 카운트
    exit_counts = result_df[result_df['exit_reason'] != '']['exit_reason'].value_counts()
    
    # 청산 사유별 평균 수익률
    exit_returns = {}
    for reason in exit_counts.index:
        mask = result_df['exit_reason'] == reason
        if 'returns' in result_df.columns:
            avg_return = result_df.loc[mask, 'returns'].mean()
            exit_returns[reason] = avg_return
    
    # 청산 사유별 평균 보유일수
    exit_holding_days = {}
    if 'holding_days' in result_df.columns:
        for reason in exit_counts.index:
            mask = result_df['exit_reason'] == reason
            avg_days = result_df.loc[mask, 'holding_days'].mean()
            exit_holding_days[reason] = avg_days
    
    return {
        'exit_counts': exit_counts.to_dict(),
        'exit_returns': exit_returns,
        'exit_holding_days': exit_holding_days,
        'total_exits': exit_counts.sum()
    }


def compare_strategies_summary(base_result, strategy_results_dict):
    """
    기본 전략 대비 각 전략의 개선도 요약
    
    Parameters:
    - base_result: 기본 전략 (익일 매도) 결과 DataFrame
    - strategy_results_dict: {전략명: DataFrame} 딕셔너리
    
    Returns:
    - DataFrame: 비교 요약 테이블
    """
    base_metrics = calculate_performance_metrics(base_result['returns'])
    
    comparison_data = []
    
    for strategy_name, result_df in strategy_results_dict.items():
        if 'returns' in result_df.columns:
            strategy_metrics = calculate_performance_metrics(result_df['returns'])
            
            # 개선도 계산
            improvement = {
                '전략': strategy_name,
                '누적수익률_개선': f"{float(strategy_metrics['누적수익률'].rstrip('%')) - float(base_metrics['누적수익률'].rstrip('%')):.1f}%p",
                '샤프비율_개선': f"{float(strategy_metrics['샤프비율']) - float(base_metrics['샤프비율']):.2f}",
                '최대낙폭_개선': f"{float(strategy_metrics['최대낙폭'].rstrip('%')) - float(base_metrics['최대낙폭'].rstrip('%')):.1f}%p",
                '평균보유일수': f"{result_df[result_df['returns'] != 0]['holding_days'].mean():.1f}일" if 'holding_days' in result_df.columns else "N/A"
            }
            
            comparison_data.append(improvement)
    
    return pd.DataFrame(comparison_data)