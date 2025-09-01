# NA 에러를 방지하는 래퍼 함수
def make_na_safe(func):
    """기존 함수를 NA 안전하게 만드는 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            if "cannot convert NA to integer" in str(e):
                # v4 함수를 대신 사용 (v4는 작동하는 것으로 확인됨)
                print(f"⚠️  NA 에러 발생, v4 함수로 대체 실행")
                # v4 함수가 전역에 있다고 가정
                if 'volatility_breakout_with_all_filters_v4' in globals():
                    return globals()['volatility_breakout_with_all_filters_v4'](*args, **kwargs)
                else:
                    raise e
            else:
                raise e
    return wrapper

# 사용 예시:
# volatility_breakout_with_all_filters_v5 = make_na_safe(volatility_breakout_with_all_filters_v5)