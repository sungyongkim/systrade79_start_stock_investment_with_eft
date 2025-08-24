"""
변동성 돌파 전략 백테스트 라이브러리
"""

from .base_strategies import (
    volatility_breakout_base,
    volatility_breakout_with_filters,
    calculate_atr
)

from .entry_strategies import (
    volatility_breakout_entry,
    adaptive_k_entry,
    double_breakout_entry,
    volume_confirmed_entry,
    momentum_filtered_entry,
    gap_adjusted_entry,
    pattern_based_entry as pattern_based_entry_strategy,
    multi_timeframe_entry,
    atr_filtered_entry,
    composite_entry
)

from .exit_strategies import (
    next_day_exit,
    atr_based_exit,
    ma_based_exit,
    momentum_score_exit,
    volatility_based_exit,
    partial_profit_exit,
    time_weighted_exit,
    bollinger_exit,
    adx_trend_exit,
    pattern_based_exit,
    composite_score_exit
)

from .utils import (
    calculate_performance_metrics,
    calculate_portfolio_returns,
    plot_strategy_comparison
)

from .combined_strategies import (
    run_backtest,
    volatility_breakout_next_day_exit,
    compare_entry_strategies,
    compare_exit_strategies
)

from .simple_backtest import (
    simple_backtest_entry_exit,
    simple_volatility_breakout_backtest
)

from .strategy_comparison import (
    get_entry_strategies_with_params,
    get_exit_strategies_with_params,
    compare_all_entry_strategies,
    compare_all_exit_strategies,
    find_best_combination
)

__all__ = [
    # Base strategies
    'volatility_breakout_base',
    'volatility_breakout_with_filters',
    'calculate_atr',
    
    # Entry strategies
    'volatility_breakout_entry',
    'adaptive_k_entry',
    'double_breakout_entry',
    'volume_confirmed_entry',
    'momentum_filtered_entry',
    'gap_adjusted_entry',
    'pattern_based_entry_strategy',
    'multi_timeframe_entry',
    'atr_filtered_entry',
    'composite_entry',
    
    # Exit strategies
    'next_day_exit',
    'atr_based_exit',
    'ma_based_exit',
    'momentum_score_exit',
    'volatility_based_exit',
    'partial_profit_exit',
    'time_weighted_exit',
    'bollinger_exit',
    'adx_trend_exit',
    'pattern_based_exit',
    'composite_score_exit',
    
    # Utils
    'calculate_performance_metrics',
    'calculate_portfolio_returns',
    'plot_strategy_comparison',
    
    # Combined strategies
    'run_backtest',
    'volatility_breakout_next_day_exit',
    'compare_entry_strategies',
    'compare_exit_strategies',
    
    # Simple backtest
    'simple_backtest_entry_exit',
    'simple_volatility_breakout_backtest',
    
    # Strategy comparison
    'get_entry_strategies_with_params',
    'get_exit_strategies_with_params',
    'compare_all_entry_strategies',
    'compare_all_exit_strategies',
    'find_best_combination'
]

__version__ = '1.0.0'