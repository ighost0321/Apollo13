"""KD for tw stock"""
def calculate_kd(df):
    """This function is used to calculate KD for stock"""
    low_min = df['low'].rolling(window=9, min_periods=1).min()  # k9 D9
    high_max = df['high'].rolling(window=9, min_periods=1).max()  # k9 D9
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    df['K'] = rsv.ewm(alpha=1 / 3).mean()
    df['D'] = df['K'].ewm(alpha=1 / 3).mean()
    return df

def filter_data(data,  begin_date: str, end_date: str, k_num: int = 20, d_num: int = 20):
    """This function is used to filter Taiwan stock dataframe"""
    """The data NUST be dataframe and cotains MUST has following information['date' 'capacity' 'open' 'high' 'low' 'close' change']"""

    filtered_df = data.loc[(data['date'] >= begin_date)& (data['date'] <= end_date)]

    # 在過濾後的資料中找到 KD 值小於或等於 20 的時間點
    kd_below_20 = filtered_df[(filtered_df["K"] <= k_num) & (filtered_df["D"] <= d_num)]

    return kd_below_20

