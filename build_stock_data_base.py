import datetime
import os
import time
import requests
import sqlite3
import pandas as pd

# KRX_API_KEY 값 추출
def GET_KRX_API_KEY():
    try:
        with open (".key","r") as f:
            for line in f:
                if "KRX_API_KEY" in line:
                    KRX_API_KEY = line.split("=")[1].strip("\"' ")
                    return KRX_API_KEY
    except FileNotFoundError:
        print("KRX_API_KEY가 존재하지 않습니다")
        return None

def init_db(conn):
    # DB 테이블 및 인덱스 초기화 (조회 속도 극대화)
    # SQL 명령을 보내고 결과를 받아오기 위해 '커서(Cursor)' 객체를 생성
    # --  (주석)
    cursor = conn.cursor()

    # 1. 테이블 생성 (숫자형 데이터는 INTEGER/REAL로 정의)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_stock_prices(
        기준일자 TEXT,    -- BAS_DD (YYYYMMDD)
        종목코드 TEXT,    -- ISU_CD (단축코드)
        종목명 TEXT,      -- ISU_NM
        시장명 TEXT,      -- MKT_NM
        종가 INTEGER,     -- TDD_CLSPRC
        시가 INTEGER,     -- TDD_OPNPRC
        고가 INTEGER,     -- TDD_HGPRC
        저가 INTEGER,     -- TDD_LWPRC
        거래량 INTEGER,   -- ACC_TRDVOL
        거래대금 INTEGER, -- ACC_TRDVAL
        시가총액 INTEGER, -- MKTCAP
        PRIMARY KEY (기준일자, 종목코드) -- 중복 수집 방지 (날짜 + 종목코드)
    )""")

    # 2. 날짜별/종목별 조회 속도를 높이기 위한 인덱스를 생성
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_기준일자 ON daily_stock_prices(기준일자)"
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_종목코드 ON daily_stock_prices(종목코드)"
    )

    conn.commit()

def build_stock_database(start_date=None, end_date=None):

    # 1. 키 값 불러오기
    KRX_API_KEY = GET_KRX_API_KEY()
    if not KRX_API_KEY:
        print("키 값을 확인해주세요")
        return 

    # 2. 수집 기간 지정
    today = datetime.datetime.today()
    if start_date == None:
        start_date = (today-datetime.timedelta(days = 365)).strftime("%Y%m%d")
    if end_date == None:
        end_date = today.strftime("%Y%m%d")

    conn = sqlite3.connect("krx_stock_data.db")

    # 3. DB 테이블 및 인덱스 생성
    init_db(conn)

    # 4. 수집 대상 영업일 산출
    all_dates = (pd.date_range(start = start_date, end = end_date)
                 .strftime("%Y%m%d").tolist())

    krx_url = "https://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd"

    # 5. 데이터 수집 시작
    for idx, day in enumerate(all_dates):
        params = {
                "AUTH_KEY" : KRX_API_KEY,
                "basDd" : day,
                "red_type" : "json"
            }
        try:
            response = requests.get(krx_url, params = params , timeout = 10)

            if response.status_code != 200:
                print(
                    f"[{day} 일] HTTP 에러 발생 (Status Code:"
                    f" {response.status_code})"
                )

                continue

            data = response.json()

            # 6 휴장일 건너 뛰기
            if "OutBlock_1" not in data or data["OutBlock_1"] == []:
                print(f"[{idx+1}/{len(all_dates)}] {day} - 장 휴장일 또는 데이터 없음")
                continue

            df = pd.DataFrame(data["OutBlock_1"])

            # 7 필요한 컬럼만 추출 및 타입 정제
            cols = ["BAS_DD", "ISU_CD", "ISU_NM", "MKT_NM", "TDD_CLSPRC", "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC", "ACC_TRDVOL", "ACC_TRDVAL", "MKTCAP"]
            df = df[cols].copy()

            # 8 종가, 시가, 고가, 저가, 거래량, 거래액, 시가총액을 숫자(정수) 타입으로 변환 및 컬러명 정리
            df["TDD_CLSPRC"] = pd.to_numeric( df["TDD_CLSPRC"], errors="coerce").fillna(0)
            df["TDD_OPNPRC"] = pd.to_numeric( df["TDD_OPNPRC"], errors="coerce").fillna(0)
            df["TDD_HGPRC"] = pd.to_numeric( df["TDD_HGPRC"], errors="coerce").fillna(0)
            df["TDD_LWPRC"] = pd.to_numeric( df["TDD_LWPRC"], errors="coerce").fillna(0)
            df["ACC_TRDVOL"] = pd.to_numeric( df["ACC_TRDVOL"], errors="coerce").fillna(0)
            df["ACC_TRDVAL"] = pd.to_numeric( df["ACC_TRDVAL"], errors="coerce").fillna(0)
            df["MKTCAP"] = pd.to_numeric( df["MKTCAP"], errors="coerce").fillna(0)
            df.columns = ["기준일자", "종목코드", "종목명", "시장명", "종가", "시가", "고가", "저가", "거래량", "거래대금", "시가총액"]

            # 9 df 데이터 sql로 저장 / multi 옵션으로 대량 Insert 속도 극대화
            df.to_sql(
                "daily_stock_prices",
                conn,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000,
            )

            conn.commit()  # 루프마다 확실하게 저장 커밋

            print(
                f"[{idx+1}/{len(all_dates)}] {day} -"
                f" {len(df):,}개 종목 적재 완료"
            )

        except requests.exceptions.RequestException as e:
            print(f"[{day} 일] 통신 에러 발생: {e}")
        except Exception as e:
            print(f"[{day} 일] 데이터 처리 중 에러: {e}")

        # 10. API 매너 대기 시간
        time.sleep(0.2)

    conn.close()
    print("데이터베이스 생성이 완료되었습니다!")


# 실행 (오늘 기준 최근 1년 치 자동 수집)
build_stock_database()