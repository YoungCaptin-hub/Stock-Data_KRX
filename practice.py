import datetime
import requests

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

KRX_API_KEY = GET_KRX_API_KEY()

today = (datetime.date.today()-datetime.timedelta(3)).strftime("%Y%m%d")

def get_krx_stock():
    krx_url = "https://data-dbg.krx.co.kr/svc/apis/sto/stk_bydd_trd"

    params = {
        "AUTH_KEY" : KRX_API_KEY,
        "basDd" : today,
        "red_type" : "json"
    }

    response = requests.get(krx_url, params = params)
    return response

response = get_krx_stock().json()
print(response["OutBlock_1"] == [])