"""KD for tw stock"""
import datetime
import yfinance as yf
import pandas as pd
import logger
import emailService


log = logger.get_log("log_config.yaml")


def calculate_kd(df):
    """This function is used to calculate KD for stock"""
    if(not df.empty):
        low_min = df["Low"].rolling(window=9, min_periods=1).min()  # k9 D9
        high_max = df["High"].rolling(window=9, min_periods=1).max()  # k9 D9
        rsv = (df["Close"] - low_min) / (high_max - low_min) * 100
        df["K"] = rsv.ewm(alpha=1 / 3).mean()
        df["D"] = df["K"].ewm(alpha=1 / 3).mean()
        return df
    else:
        return None


def filter_data(data,  begin_date: str, end_date: str, k_num: int = 20, d_num: int = 20):
    """This function is used to filter Taiwan stock dataframe"""
    """The data NUST be dataframe and cotains MUST has following information['date' 'capacity' 'open' 'high' 'low' 'close' change']"""

    filtered_df = data.loc[begin_date:end_date]

    # 在過濾後的資料中找到 KD 值小於或等於 20 的時間點
    kd_below_20 = filtered_df[(filtered_df["K"] <= k_num) & (filtered_df["D"] <= d_num)]

    return kd_below_20


def Find_KD20(filename: str, output: str, begin_date: str, end_date: str) -> bool:

    try:
        with open(filename, "r", encoding="utf8") as f:
            companies = f.read().split(",")
    except IOError as e:
        log.exception(e)
        return False
    except Exception as e:
        log.exception(e)
        return False

    # 計算當前日期和一個月前的日期
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=90)

    # 下載股票數據
    total_df = None
    for company in companies:
        code, name = company.split("|")
        df = yf.download(
            code,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
        )
        # 計算 KD 指標
        df = calculate_kd(df)

        # 找到並列印 KD 值小於或等於 20 的時間點
        kd_below_20 = filter_data(df, begin_date, end_date, k_num=30, d_num=30)

        if not kd_below_20.empty:
            kd_below_20['code'] = code
            kd_below_20['name'] = name
            total_df = pd.concat([total_df, kd_below_20[["code", "name", "K", "D", "Close"]]])
            
    total_df.to_excel(output, index=True, engine='openpyxl')    
    return False


if __name__ == "__main__":
    # CMD: python days_kd_lite.py > yyyyMMdd.txt
    # 計算系統日和系統日-14的日期
    # 因為yahoo設定的downlaod日期區間是"不"包括start & end，所以若是要抓2個禮拜的日期，要故意抓大一點區間
    now = datetime.datetime.now()
    before = now - datetime.timedelta(days=15)
    now = now.strftime("%Y-%m-%d")
    before = before.strftime("%Y-%m-%d")
    log.info("Start to work...")
    #預設檔名
    save_file = f'kd20_TW_{now}.xlsx'

    Find_KD20('stock.csv', save_file, begin_date=before, end_date=now)  # 先跑上市股票
    
    # 將結果寄出
    attachments = [save_file]
    # emailService.send_mail(attaches=attachments)

    log.info("Mission completed successfully")
