# Stock-Data_KRX

KRX(한국거래소) 정보데이터시스템 Open API를 이용해 일별 주식 시세 데이터를 수집하고,
SQLite 데이터베이스(`krx_stock_data.db`)에 누적 저장하는 파이썬 스크립트입니다.

## 주요 기능

- KRX Open API(`/svc/apis/sto/stk_bydd_trd`)로 일자별 전 종목 시세 조회
- 이미 수집된 날짜는 건너뛰고, 아직 수집되지 않은 영업일만 증분 수집
- 종가, 시가, 고가, 저가, 거래량, 거래대금, 시가총액 등 주요 컬럼을 정제하여 SQLite에 저장
- `(기준일자, 종목코드)` 기준 중복 저장 방지 및 조회 속도를 위한 인덱스 자동 생성
- 최근 1년치 데이터만 유지하도록, 갱신 시 1년이 지난 과거 데이터는 자동 삭제

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

### 1. 최초 데이터베이스 구축

`krx_stock_data.db`가 없거나 처음부터 데이터를 쌓고 싶다면 실행합니다.
기본값으로 실행하면 오늘 기준 최근 1년간의 데이터를 수집합니다.

```bash
python build_stock_data_base.py
```

기간을 직접 지정하고 싶다면 `build_stock_database` 함수를 사용하세요.

```python
from build_stock_data_base import build_stock_database

build_stock_database(start_date="20240101", end_date="20241231")
```

### 2. 데이터 갱신 (증분 수집)

이미 구축된 데이터베이스를 최신 상태로 유지하고 싶을 때 실행합니다.
마지막으로 수집된 날짜 이후의 영업일만 이어서 수집하고,
수집 시점 기준으로 1년이 지난 과거 데이터는 자동으로 삭제하여
데이터베이스가 항상 "최근 1년" 범위를 유지하도록 합니다.

```bash
python renew_stock_data.py
```

정기적으로(예: 매일 장 마감 후) cron 등으로 실행하면 별도 조작 없이
데이터베이스를 최신 상태로 유지할 수 있습니다.

### 3. API 응답 확인 (테스트용)

`practice.py`는 특정 날짜의 API 응답이 정상적으로 오는지(휴장일 여부 등)
간단히 확인하기 위한 테스트 스크립트입니다.

```bash
python practice.py
```

## 데이터베이스 스키마

`daily_stock_prices` 테이블 (컬럼명은 한글로 저장되며, 괄호는 KRX API 원본 필드명입니다)

| 컬럼 | 설명 |
| --- | --- |
| 기준일자 | 기준일자 (YYYYMMDD) (BAS_DD) |
| 종목코드 | 종목코드 (예: 005930) (ISU_CD) |
| 종목명 | 종목명 (예: 삼성전자) (ISU_NM) |
| 시장명 | 시장 구분 (코스피/코스닥 등) (MKT_NM) |
| 종가 | 종가 (TDD_CLSPRC) |
| 시가 | 시가 (TDD_OPNPRC) |
| 고가 | 고가 (TDD_HGPRC) |
| 저가 | 저가 (TDD_LWPRC) |
| 거래량 | 누적 거래량 (ACC_TRDVOL) |
| 거래대금 | 누적 거래대금 (ACC_TRDVAL) |
| 시가총액 | 시가총액 (MKTCAP) |

Primary Key: `(기준일자, 종목코드)`

## 프로젝트 구조

```
.
├── build_stock_data_base.py  # DB 최초 초기화 및 전체 기간 데이터 수집
├── renew_stock_data.py       # 신규 영업일 증분 수집 및 1년 초과 데이터 삭제
├── practice.py                # API 응답 확인용 테스트 스크립트
├── krx_stock_data.db          # 수집된 데이터가 저장되는 SQLite DB (실행 시 생성)
├── .key                        # KRX API 인증키 (직접 생성, git 미포함)
└── requirements.txt
```

## 라이선스

[MIT License](LICENSE)
