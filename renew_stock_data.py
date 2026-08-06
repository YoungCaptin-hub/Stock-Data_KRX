import sqlite3
import requests
import time
import pandas as pd
import datetime

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

def renew_stock_data():
    # 1. 키 값 불러오기
    KRX_API_KEY = GET_KRX_API_KEY()
    if not KRX_API_KEY:
        print("키 값을 확인해주세요")
        return 
    conn = sqlite3.connect("krx_stock_data.db")

    # 2. 총 수집 기간 설정
    today = datetime.datetime.today()
    start_date = (today - datetime.timedelta(days = 365)).strftime("%Y%m%d")
    end_date = today.strftime("%Y%m%d")

    all_dates = (pd.date_range(start = start_date, end = end_date).strftime("%Y%m%d").tolist())

    # 3. 이미 수집된 날짜 조회
    saved_dates = set(
        pd.read_sql(
        "SELECT DISTINCT BAS_DD FROM daily_stock_prices", conn)["BAS_DD"]
        )

    # 4. 중복 수집 방지
    target_dates = [d for d in all_dates if d not in saved_dates and d > max(saved_dates)]
    print(f"수집 기간: {start_date} - {end_date}")
    print(f"{len(all_dates)} 일 중에서 {len(saved_dates)}개 완료 /"
          f"{len(target_dates)}개 신규 수집 진행")

    krx_url = "https://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd"
    
    # 5. 데이터 수집 시작
    for idx, day in enumerate(target_dates):
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
            df = pd.DataFrame(data["OutBlock_1"])

            # 6. 휴장일 건너 뛰기
            if data["OutBlock_1"] == [] :
                print(f" {day} 장 휴장일 또는 당일 데이터는 4시 이후 업데이트 가능")
                continue

            # 7. 필요한 컬럼만 추출 및 타입 정제
            cols = ["BAS_DD", "ISU_CD", "ISU_NM", "MKT_NM", "SECT_TP_NM", "TDD_CLSPRC", "TDD_OPNPRC", "ACC_TRDVOL", "ACC_TRDVAL", "MKTCAP"]
            df = df[cols].copy()
            
            # 8. 종가, 시가, 거래량, 거래액, 시가총액을 숫자(정수) 타입으로 변환
            df["TDD_CLSPRC"] = pd.to_numeric( df["TDD_CLSPRC"], errors="coerce").fillna(0)
            df["TDD_OPNPRC"] = pd.to_numeric( df["TDD_OPNPRC"], errors="coerce").fillna(0)
            df["ACC_TRDVOL"] = pd.to_numeric( df["ACC_TRDVOL"], errors="coerce").fillna(0)
            df["ACC_TRDVAL"] = pd.to_numeric( df["ACC_TRDVAL"], errors="coerce").fillna(0)
            df["MKTCAP"] = pd.to_numeric( df["MKTCAP"], errors="coerce").fillna(0)
            
            # 9. df 데이터 sql로 저장 / multi 옵션으로 대량 Insert 속도 극대화
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
                f"[{idx+1}/{len(target_dates)}] {day} -"
                f" {len(df):,}개 종목 적재 완료"
            )

    
        except requests.exceptions.RequestException as e:
            print(f"[{day} 일] 통신 에러 발생: {e}")
        except Exception as e:
            print(f"[{day} 일] 데이터 처리 중 에러: {e}")

        # 10. API 매너 대기 시간
        time.sleep(0.2)
    
    if not target_dates:
        print("이미 모든 데이터는 최신 상태입니다.")
        conn.close()
        return

    # 11. 1년 전 데이터 삭제
    conn = sqlite3.connect("krx_stock_data.db")
    cursor =conn.cursor()

    cutoff_date = (today - datetime.timedelta(days=365)).strftime("%Y%m%d")

        
    cursor.execute("DELETE FROM daily_stock_prices WHERE BAS_DD < ? " , (cutoff_date,))
        
    # 12. 지워진 행(Row) 수 확인
    deleted_rows = cursor.rowcount
    print(f" 제거한 행수 : {deleted_rows} ")
        
    # 13. 변경사항 최종 저장
    conn.commit()
    conn.close()

renew_stock_data()