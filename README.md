# 주식투자 ETF로 시작하라 - 백테스트 프로젝트

시스트레이드79의 "주식투자 ETF로 시작하라" 서적을 기반으로 한 백테스트 실습 프로젝트입니다.

## 📚 프로젝트 개요

이 프로젝트는 ETF를 활용한 다양한 투자 전략을 백테스트하고 분석하는 것을 목표로 합니다. 변동성 돌파 전략을 기반으로 여러 기술적 지표를 조합하여 수익률을 개선하는 방법을 탐구합니다.

## 🚀 주요 전략

### Part4 - 변동성 돌파 전략 시리즈

1. **기본 변동성 돌파 전략**
   - 전일 변동폭의 일정 비율을 돌파 시 매수
   - ATR(Average True Range)을 활용한 변동성 측정

2. **ADX 필터 전략** (`02_변동성_돌파_ADX_필터_전략.ipynb`)
   - ADX(Average Directional Index)로 추세 강도 필터링
   - 강한 추세 시장에서만 진입

3. **ADX + Chaikin 전략** (`03_변동성_돌파_ADX_Chaikin_전략.ipynb`)
   - Chaikin Money Flow로 자금 흐름 분석 추가
   - 매수/매도 압력 고려

4. **상대 모멘텀 전략** (`04_변동성_돌파_상대모멘텀_전략.ipynb`)
   - 여러 ETF 중 상대적으로 강한 모멘텀 종목 선택
   - 포트폴리오 최적화

5. **다중기간 가중치 모멘텀** (`05_변동성_돌파_상대모멘텀_다중기간_가중치_모멘텀_전략.ipynb`)
   - 단기/중기/장기 모멘텀 종합 평가
   - 기간별 가중치 최적화

6. **절대모멘텀 + 변동성 전략** (`06_변동성_돌파_ADX_Chaikin_절대모멘텀_변동성_전략.ipynb`)
   - 절대 모멘텀으로 시장 타이밍 결정
   - 변동성 기반 포지션 사이징

7. **OBV(On Balance Volume) 전략** (`07_01_변동성_돌파_OBV.ipynb`, `07_02_변동성_돌파_OBV.ipynb`)
   - 거래량 지표를 활용한 매수/매도 압력 분석
   - OBV 추세와 가격 추세의 다이버전스 활용
   - 거래량 확인을 통한 돌파 신호 검증

## 📁 프로젝트 구조

```
.
├── Part4/
│   ├── 00_실습파일.ipynb                    # 기본 실습 템플릿
│   ├── 01~06_변동성_돌파_*.ipynb           # 전략별 백테스트 노트북
│   ├── 07_01~02_변동성_돌파_OBV.ipynb      # OBV 거래량 전략
│   ├── backtest_strategy/                   # 백테스트 라이브러리
│   │   ├── base_strategies.py              # 기본 전략 클래스
│   │   ├── entry_strategies.py             # 진입 전략
│   │   ├── exit_strategies.py              # 청산 전략
│   │   └── combined_strategies.py          # 조합 전략
│   ├── 4_1_변동성_돌파_단타_전략/          # 단타 전략 상세 분석
│   │   └── knowledge_base/                  # 전략 설명 문서
│   └── 4_2_손절과_자금관리/                # 리스크 관리
│       └── knowledge_base/                  # 손절/자금관리 문서
└── README.md
```

## 🛠️ 설치 및 실행

### 필요 라이브러리
```bash
pip install pandas numpy matplotlib yfinance ta pandas-ta
```

### 실행 방법
1. Jupyter Notebook 실행
```bash
jupyter notebook
```

2. Part4 디렉토리의 원하는 전략 노트북 열기

3. 순차적으로 셀 실행

## 📊 백테스트 프레임워크

프로젝트에 포함된 `backtest_strategy` 모듈을 사용하여 자신만의 전략을 구현할 수 있습니다:

```python
from backtest_strategy import VolatilityBreakoutADX

# 전략 초기화
strategy = VolatilityBreakoutADX(
    breakout_ratio=0.5,
    adx_threshold=25,
    adx_period=14
)

# 백테스트 실행
results = strategy.backtest(data, initial_capital=10000)
```

## 📈 주요 성과 지표

각 전략은 다음 지표들로 평가됩니다:
- 총 수익률 (Total Return)
- 샤프 비율 (Sharpe Ratio)
- 최대 낙폭 (Maximum Drawdown)
- 승률 (Win Rate)
- 손익비 (Profit/Loss Ratio)

## 🔍 주요 인사이트

1. **단순 변동성 돌파 < ADX 필터 추가**
   - 횡보장에서의 가짜 신호 제거 효과

2. **모멘텀 지표 조합의 중요성**
   - 단일 지표보다 복합 지표가 안정적

3. **자금관리의 핵심**
   - ATR 기반 동적 손절선 설정
   - 포지션 사이징의 중요성

4. **거래량 지표의 활용**
   - OBV를 통한 스마트머니 추적
   - 가격 돌파 시 거래량 확인 필수

## 🤝 기여하기

이 프로젝트는 학습 목적으로 만들어졌습니다. 개선사항이나 새로운 전략 아이디어가 있다면 자유롭게 기여해주세요.

## 📖 참고 자료

- 시스트레이드79, 『주식투자 ETF로 시작하라』
- [프로젝트 관련 블로그/문서 링크]

## ⚠️ 주의사항

- 이 프로젝트의 백테스트 결과는 과거 데이터 기반이며, 미래 수익을 보장하지 않습니다
- 실제 투자 시에는 충분한 검토와 리스크 관리가 필요합니다
- 모든 투자의 책임은 투자자 본인에게 있습니다

## 📝 라이선스

이 프로젝트는 교육 목적으로 제공되며, 상업적 사용 시 원저자의 허락이 필요합니다.