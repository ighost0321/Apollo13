"""pick up potential stars TW stock """
import logger


def is_potential_star(previous_day, current_day, log, multiple: float = 3.0) -> bool:
    """Identify potential bull stocks based on price increase and volume spike.
    
    Args:
        previous_day: Previous trading day's data (DataFrame or Series)
        current_day: Current trading day's data (DataFrame or Series)
        log: Logger instance
        multiple: Volume spike multiplier threshold (default: 3.0)
        
    Returns:
        bool: True if stock is a potential star, False otherwise
    """
    if type(log).__name__ != "Logger":
        log = logger.get_log("log_config.yaml")

    if previous_day.empty or current_day.empty:
        log.info("input is empty!")
        return False

    log.info("判斷最近一筆資料的收盤價是否大於前一天")
    price_change = float(current_day.loc["Close"]) - float(previous_day.loc["Close"])
    if price_change > 0:
        log.info("股價收盤價大於前一天收盤價，判斷股價上漲")
        log.info("再判斷最近一筆成交量是否大於%.1f倍", multiple)
        volume_spike = float(current_day.loc["Volume"]) > (
            float(previous_day.loc["Volume"]) * multiple
        )
        if volume_spike:
            log.info("最近一筆成交量大於前一天成交量%.1f倍，為潛在飆股", multiple)
            return True
        else:
            log.info("最近一筆資料的成交量沒有大於前一天%.1f倍", multiple)
    else:
        log.info("最近一筆資料的收盤價沒有大於前一天，股價下跌")
    return False
