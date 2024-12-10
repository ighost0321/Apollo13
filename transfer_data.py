"""This application transfer data from 公開資訊站"""
import logger
import pandas as pd

log = logger.get_log("csv_log_config.yaml")


def transfer_tw_data(
    csv_file: str,
    save_file: str = "data1.csv",
    extension: str = ".TW",
    is_rewritable: bool = True,
    addtional_func=None,
) -> bool:
    """(Yahoo)This application ONLY handles a file called tw.csv (上市). These two files need to encoded with cp950."""
    report_list = []
    try:
        with open(csv_file, "r", encoding="utf8", newline="") as csv:
            contents = csv.readlines()
    except Exception as e:
        log.exception(e)
        return False
    else:
        # 宣告報到 list
        # 逐行讀取 CSV 檔案
        for row in contents:
            # 判斷第一行是否為數字
            company_code = row.split(",")[0].replace('"', "")
            company_name = row.split(",")[2].replace('"', "")
            industry_name = row.split(",")[3].replace('"', "")
            if company_code.isdigit():
                # 將該列資料新增到報到 list 中
                report_list.append(f"{company_code}{extension},{company_name},{industry_name}")

    if report_list:
        report_list = set(report_list)
        if addtional_func:
            report_list = addtional_func(report_list)

        try:
            if is_rewritable:
                mode = "w"
            else:
                mode = "a"

            with open(save_file, mode, encoding="utf-8") as file:
                # 寫入報到 list
                file.write(str(report_list).strip("[]").replace("'", ""))

        except IOError as e:
            log.exception("Error occurred: %s", e)
            return False
        else:
            return True
    else:
        log.info("source does not contain proper data to fetchg!")
        return False

def transfer_data(
    csv_file: str,
    save_file: str = "data1.csv",
    extension: str = ".TW",
    is_rewritable: bool = True,
    addtional_func=None,
) -> list:
    """(Yahoo)This application ONLY handles a file called tw.csv (上市). These two files need to encoded with cp950."""
    report_list = []
    try:
        with open(csv_file, "r", encoding="utf8", newline="") as csv:
            contents = csv.readlines()
    except Exception as e:
        log.exception(e)
        return False
    else:
        # 宣告報到 list
        # 逐行讀取 CSV 檔案
        for row in contents:
            # 判斷第一行是否為數字
            company_code = row.split(",")[0].replace('"', "")
            company_name = row.split(",")[2].replace('"', "")
            industry_name = row.split(",")[3].replace('"', "")
            if company_code.isdigit():
                # 將該列資料新增到報到 list 中
                report_list.append(f'{company_code}{extension},{company_name},{industry_name}')

    if report_list:
        return list(set(report_list))
    else:
        log.info("source does not contain proper data to fetchg!")
        return None


if __name__ == "__main__":
    fn = lambda x: [",".join(map(lambda item: item, x))]
    #先處裡上市股票，股票清單為.csv
    #SAVE_FILE = transfer_tw_stock_data(files,addtional_func=fn)
    file_TW = "stock_TW.csv"
    file_TWO = "stock_TWO.csv"
    #上市
    stock_list = transfer_data("twse_20240527.csv", save_file=file_TW,addtional_func=fn) # for Yahoo
    #Confirm the numbers of transfered data in file. 
    if stock_list:
        print(f"numbers of stock_list: {len(stock_list)}")
    
    #再處裡上櫃股票，股票清單為.csm
    stock_TWO_list = transfer_data(
        "tpex_20240527.csv",
        save_file=file_TWO,
        extension=".TWO",
        addtional_func=fn
    )
    if stock_TWO_list:
        print(f"numbers of stock_TWO_list: {len(stock_TWO_list)}")

    if stock_TWO_list:
        stock_list += stock_TWO_list
        print(f"numbers of stock_list: {len(stock_list)}")
    else:
        print("Failed to transfer data.")
    

    #export as dataframe
    # df = pd.DataFrame(stock_list, columns=['code','name','industry'])

    # print(df)

    # #最後將他們合而為一
    try:
        with open("stock.csv", "w", encoding="utf8") as f:
            for row in stock_list:
                f.write(row)
                f.write("\n")

    except IOError as e:
        log.exception(e)
    except Exception as e:
        log.exception(e)

    df = pd.read_csv("stock.csv", names=["code", "name", "industry"])
    #filter data
    filters = ["電子零組件業", "數位雲端", "半導體業", "電子通路業", "電腦及週邊設備業", "其他電子業", "光電業", "電機機械", "資訊服務業", "電器電纜"]
    df = df[df['industry'].isin(filters)]
    print(df)
    #finally, write to _stock.csv file
    df.to_csv("_stock.csv", index=False, header=False)

    # #Confirm the numbers of transfered data in file.  
    # try:
    #     with open("stock.csv", "r", encoding="utf8") as f:
    #         string = f.read()
    #         array = string.split(",")
    #         print(f"numbers of stock.csv: {len(array)}")
    # except IOError as e:
    #     print("stock.csv File not found:")
