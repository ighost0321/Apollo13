""" Main function"""
import os
import datetime
import pandas as pd
import yfinance
import kd_tools as kd
import potential_starts as ps
import logger
import emailService



if __name__ == "__main__":
    log = logger.get_log("log_config.yaml")
    current_dir = f"{os.path.curdir}{os.sep}reports"
    default_KD_limits = 30
    default_days = 7

    # Check report directory exits or not
    if not current_dir or not os.path.isdir(current_dir):
        current_dir = f"{os.path.curdir}{os.sep}reports"
        try:
            os.makedirs(current_dir)
        except OSError as e:
            log.exception(e)

    # 計算當前日期和一個月前的日期
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=90)
    tickers = [] #store tw stock id only
    tw_stock_list = [] #store tw stock infomation
    try:
        with open("_stock.csv", "r", encoding="utf8") as f:
                companies = f.readlines()
    except IOError as e:
        log.exception(e)
    except Exception as e:
        log.exception(e)
    else:
        # 計算當前日期和一個月前的日期
        # 下載股票數據
        total_kd_df = None  # Store kd data
        total_stars_df = None  # Store potential stars data
        tickers_dict = {}

        tickers_dict = {company.split(',')[0]: company for company in companies} 
        tickers = list(tickers_dict.keys())
        df = yfinance.download(tickers, group_by="ticker", period="1mo")
        # df = yfinance.download("2330.TW", group_by="ticker", period="1mo")
        d = {idx: gp.T for idx, gp in df.T.groupby(level=0)}
        
        for key, value in d.items():
            value.columns = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
            ################################################################
            #取得股票資訊
            ################################################################
            ticker_info = tickers_dict.get(key)
            if len(ticker_info) == 0:
                continue
            ticker_id = key
            ticker_name = ticker_info.split(',')[1]
            ticker_industry = ticker_info.split(',')[2].replace("\n","")
            value['id'] = ticker_id
            value['name'] = ticker_name
            value['industry'] = ticker_industry
            ###############################################################
            #找到並列印 KD 值小於或等於設定的時間
            ###############################################################
            df_kd = kd.calculate_kd(value)
            kd_under_level = kd.filter_data_days(df_kd, days_in_advance=default_days, d_num=default_KD_limits)
            kd_under_level = kd_under_level[["id", "name", "industry", "Close", "K", "D", "Volume"]]
            total_kd_df = pd.concat(
                    [total_kd_df, kd_under_level]
                )
            ################################################################
            # 尋找潛在飆股(potential stars)
            ################################################################
            tmp_df = value.tail(2)
            if len(tmp_df) >= 2:
                df1 = tmp_df.iloc[0]
                df2 = tmp_df.iloc[1]
                if ps.is_potential_star(df1, df2, log, 4.2):
                    total_stars_df = pd.concat(
                    [
                        total_stars_df,
                        tmp_df[["id", "name", "industry", "Close", "K", "D", "Volume"]],
                    ])
            

        # Final
        # save kd data to csv
        excel_kd_filename = (
            f'kd20_TW_{datetime.datetime.now().strftime("%Y-%m-%d")}.xlsx'
        )
        csv_kd_filename = f'kd20_TW_{datetime.datetime.now().strftime("%Y-%m-%d")}.csv'
        excel_stars_filename = (
            f'stars_TW_{datetime.datetime.now().strftime("%Y-%m-%d")}.xlsx'
        )
        csv_stars_filename = (
            f'stars_TW_{datetime.datetime.now().strftime("%Y-%m-%d")}.csv'
        )
        if total_kd_df is not None and not total_kd_df.empty:
            total_kd_df["id"] = total_kd_df["id"].str.replace(r"\.TWO$|\.TW$", "", regex=True)
            csv_kd_full_path = f"{current_dir}{os.sep}{csv_kd_filename}"
            excel_kd_full_path = f"{current_dir}{os.sep}{excel_kd_filename}"
            total_kd_df.to_csv(csv_kd_full_path, sep=",", index=True, header=True)
            total_kd_df.to_excel(excel_kd_full_path, index=True, engine="openpyxl")

        #save stars data to csv
        if total_stars_df is not None and not total_stars_df.empty:
            total_stars_df["id"] = total_stars_df["id"].str.replace(r"\.TWO$|\.TW$", "", regex=True)
            csv_stars_full_path = f"{current_dir}{os.sep}{csv_stars_filename}"
            excel_stars_full_path = f"{current_dir}{os.sep}{excel_stars_filename}"
            total_stars_df.to_csv(
                csv_stars_full_path, sep=",", index=True, header=True
            )
            total_stars_df.to_excel(
                excel_stars_full_path, index=True, engine="openpyxl"
            )

        # transform csv to xlsx
        # send email
        # 將結果寄出
        try:
            attachments = []
            if os.path.isfile(excel_kd_full_path):
                attachments.append(excel_kd_full_path)
            if os.path.isfile(excel_stars_full_path):
                attachments.append(excel_stars_full_path)
        except UnboundLocalError as e:
            log.exception(e)
        except Exception as e:
            log.exception(e)
        
        if attachments:
            emailService.send_mail(log=log, attaches=attachments)

        log.info("Mission completed successfully")
