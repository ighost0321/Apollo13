"""KD for tw stock"""
import datetime

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

def filter_data_days(data,  days_in_advance: int = 1, k_num: int = 20, d_num: int = 20):
    """This function is used to filter Taiwan stock dataframe"""
    today = datetime.datetime.now()
    before = today - datetime.timedelta(days=days_in_advance)
    end = today.strftime("%Y-%m-%d")
    begin = before.strftime("%Y-%m-%d")

    return filter_data(data, begin, end, k_num, d_num)

def filter_data(data,  begin_date: str, end_date: str, k_num: int = 20, d_num: int = 20):
    """This function is used to filter Taiwan stock dataframe"""

    filtered_df = data.loc[begin_date:end_date]

    # 在過濾後的資料中找到 KD 值小於或等於 20 的時間點
    kd_below_20 = filtered_df[(filtered_df["K"] <= k_num) & (filtered_df["D"] <= d_num)]

    return kd_below_20
