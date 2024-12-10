"""pick up potential stars TW stock """
import logger


def is_potential_star(df1: any, df2: any, log: any, multiple: float = 3.0) -> bool:

    if type(log).__name__ != "Logger":
        log = logger.get_log("log_config.yaml")

    if df1.empty or df2.empty:
        log.info("input is empty!")
        return False

    log.info("判斷最近一筆資料的收盤價是否大於前一天")
    chnages = float(df1.loc["Close"]) - float(df2.loc["Close"])
    if chnages > 0:
        log.info("股價收盤價大於等於前一天收盤價，判斷股價上漲")
        log.info("再判斷最近一筆成交量是否大於%d倍", multiple)
        flag = float(df1.loc["Volume"]) * multiple < float(df2.loc["Volume"])
        if flag:
            log.info("最近一筆成交量大於前一天成交量%f倍", multiple)
            return True
        else:
            log.info("最近一筆資料的成交量沒有大於前一天%f倍", multiple)
    else:
        log.info("最近一筆資料的收盤價沒有大於前一天，股價下跌")
    return False