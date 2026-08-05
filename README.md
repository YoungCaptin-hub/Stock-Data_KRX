# Stock-Data_KRX

KRX(한국거래소) 정보데이터시스템 Open API를 이용해 일별 주식 시세 데이터를 수집하고,
SQLite 데이터베이스(`krx_stock_data.db`)에 누적 저장하는 파이썬 스크립트입니다.

## 주요 기능

- KRX Open API(`/svc/apis/sto/stk_bydd_trd`)로 일자별 전 종목 시세 조회
- 이미 수집된 날짜는 건너뛰고, 아직 수집되지 않은 영업일만 증분 수집
- 종가, 시가, 거래량, 거래대금, 시가총액 등 주요 컬럼을 정제하여 SQLite에 저장
- `(기준일자, 종목코드)` 기준 중복 저장 방지 및 조회 속도를 위한 인덱스 자동 생성

## 요구 사항

- Python 3.10 이상
- KRX 정보데이터시스템 Open API 인증키
  ([data.krx.co.kr](https://data.krx.co.kr)에서 발급)

## 설치

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## API 키 설정

프로젝트 루트에 `.key` 파일을 만들고 아래와 같이 발급받은 인증키를 입력합니다.
(`.key`는 `.gitignore`에 포함되어 git에 커밋되지 않습니다.)

```
KRX_API_KEY = "발급받은_인증키"
```

## 사용법

```bash
python data_base.py
```

기본값으로 실행하면 오늘 기준 최근 1년간의 데이터를 수집하여
`krx_stock_data.db`에 저장합니다. 이미 수집된 날짜는 자동으로 건너뛰고
신규 영업일만 이어서 수집합니다.

기간을 직접 지정하고 싶다면 `build_stock_database` 함수를 사용하세요.

```python
from data_base import build_stock_database

build_stock_database(start_date="20240101", end_date="20241231")
```

## 데이터베이스 스키마

`daily_stock_prices` 테이블

| 컬럼 | 설명 |
| --- | --- |
| BAS_DD | 기준일자 (YYYYMMDD) |
| ISU_CD | 종목코드 (예: 005930) |
| ISU_NM | 종목명 (예: 삼성전자) |
| MKT_NM | 시장 구분 (코스피/코스닥 등) |
| SECT_TP_NM | 소속부 명칭 |
| TDD_CLSPRC | 종가 |
| TDD_OPNPRC | 시가 |
| ACC_TRDVOL | 누적 거래량 |
| ACC_TRDVAL | 누적 거래대금 |
| MKTCAP | 시가총액 |

Primary Key: `(BAS_DD, ISU_CD)`

## 프로젝트 구조

```
.
├── data_base.py        # DB 초기화 및 데이터 수집 메인 로직
├── practice.py          # API 응답 확인용 테스트 스크립트
├── krx_stock_data.db    # 수집된 데이터가 저장되는 SQLite DB (실행 시 생성)
├── .key                  # KRX API 인증키 (직접 생성, git 미포함)
└── requirements.txt
```

## 라이선스

[MIT License](LICENSE)
