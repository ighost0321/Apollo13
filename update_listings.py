import csv
import glob
import json
import logging
import os
import sys
import time
import urllib.request
from datetime import date


TWSE_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
TPEX_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"

# 重試設定
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒


def _setup_logging():
    """設定 logging，同時輸出到檔案和控制台"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"fetch_{date.today().strftime('%Y%m%d')}.log")
    
    # 設定 logging 格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def _request_json(url, logger, max_retries=MAX_RETRIES):
    """發送 HTTP 請求並重試"""
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"請求 {url} (嘗試 {attempt}/{max_retries})")
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Apollo13/1.0"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode("utf-8")
            logger.info(f"成功從 {url} 獲取資料")
            return json.loads(data)
        except urllib.error.URLError as e:
            logger.warning(f"網路錯誤 (嘗試 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"等待 {RETRY_DELAY} 秒後重試...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"達到最大重試次數，請求失敗: {url}")
                raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析錯誤: {e}")
            raise
        except Exception as e:
            logger.error(f"未預期的錯誤 (嘗試 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                logger.info(f"等待 {RETRY_DELAY} 秒後重試...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def _latest_header(pattern, fallback, logger):
    candidates = sorted(glob.glob(pattern))
    if not candidates:
        logger.info(f"找不到現有的檔案 ({pattern})，使用預設 header")
        return fallback
    latest = candidates[-1]
    logger.info(f"從現有檔案讀取 header: {latest}")
    with open(latest, "r", encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f))


def _build_headers():
    # Unicode-safe header keys (ASCII-only source).
    h = {
        "code": "\u516c\u53f8\u4ee3\u865f",
        "name": "\u516c\u53f8\u540d\u7a31",
        "abbr": "\u516c\u53f8\u7c21\u7a31",
        "industry": "\u7522\u696d\u985e\u5225",
        "foreign": "\u5916\u570b\u4f01\u696d\u8a3b\u518a\u5730\u570b",
        "address": "\u4f4f\u5740",
        "ubn": "\u71df\u5229\u4e8b\u696d\u7d71\u4e00\u7de8\u865f",
        "chair": "\u8463\u4e8b\u9577",
        "gm": "\u7e3d\u7d93\u7406",
        "spokes": "\u767c\u8a00\u4eba",
        "spokes_title": "\u767c\u8a00\u4eba\u8077\u7a31",
        "deputy": "\u4ee3\u7406\u767c\u8a00\u4eba",
        "tel": "\u7e3d\u6a5f\u96fb\u8a71",
        "inc_date": "\u6210\u7acb\u65e5\u671f",
        "list_date_twse": "\u4e0a\u5e02\u65e5\u671f",
        "list_date_tpex": "\u4e0a\u6ac3\u65e5\u671f",
        "par": "\u666e\u901a\u80a1\u6bcf\u80a1\u9762\u984d",
        "capital": "\u5be6\u6536\u8cc7\u672c\u984d(\u5143)",
        "issue_shares": "\u5df2\u767c\u884c\u666e\u901a\u80a1\u6578\u6216TDR\u539f\u767c\u884c\u80a1\u6578",
        "private": "\u79c1\u52df\u666e\u901a\u80a1(\u80a1)",
        "pref": "\u7279\u5225\u80a1(\u80a1)",
        "fr_type": "\u7de8\u88fd\u8ca1\u52d9\u5831\u544a\u985e\u578b",
        "dist_freq": "\u666e\u901a\u80a1\u76c8\u9918\u5206\u6d3e\u6216\u865b\u640d\u64a5\u88dc\u983b\u7387",
        "div_level": "\u666e\u901a\u80a1\u5e74\u5ea6(\u542b\u7b2c4\u5b63\u6216\u5f8c\u534a\u5e74\u5ea6)\u73fe\u91d1\u80a1\u606f\u53ca\u7d05\u5229\u6c7a\u8b70\u5c64\u7d1a",
        "agent": "\u80a1\u7968\u904e\u6236\u6a5f\u69cb",
        "agent_tel": "\u904e\u6236\u96fb\u8a71",
        "agent_addr": "\u904e\u6236\u5730\u5740",
        "firm": "\u7c3d\u8b49\u6703\u8a08\u5e2b\u4e8b\u52d9\u6240",
        "cpa1": "\u7c3d\u8b49\u6703\u8a08\u5e2b1",
        "cpa2": "\u7c3d\u8b49\u6703\u8a08\u5e2b2",
        "eng_abbr": "\u82f1\u6587\u7c21\u7a31",
        "eng_addr": "\u82f1\u6587\u901a\u8a0a\u5730\u5740",
        "fax": "\u50b3\u771f\u6a5f\u865f\u78bc",
        "email": "\u96fb\u5b50\u90f5\u4ef6\u4fe1\u7bb1",
        "url": "\u516c\u53f8\u7db2\u5740",
        "ir_contact": "\u6295\u8cc7\u4eba\u95dc\u4fc2\u806f\u7d61\u4eba",
        "ir_title": "\u6295\u8cc7\u4eba\u95dc\u4fc2\u806f\u7d61\u4eba\u8077\u7a31",
        "ir_tel": "\u6295\u8cc7\u4eba\u95dc\u4fc2\u806f\u7d61\u96fb\u8a71",
        "ir_email": "\u6295\u8cc7\u4eba\u95dc\u4fc2\u806f\u7d61\u96fb\u5b50\u90f5\u4ef6",
        "stake_url": "\u516c\u53f8\u7db2\u7ad9\u5167\u5229\u5bb3\u95dc\u4fc2\u4eba\u5c08\u5340\u7db2\u5740",
    }

    twse_header = [
        h["code"],
        h["name"],
        h["abbr"],
        h["industry"],
        h["foreign"],
        h["address"],
        h["ubn"],
        h["chair"],
        h["gm"],
        h["spokes"],
        h["spokes_title"],
        h["deputy"],
        h["tel"],
        h["inc_date"],
        h["list_date_twse"],
        h["par"],
        h["capital"],
        h["issue_shares"],
        h["private"],
        h["pref"],
        h["fr_type"],
        h["dist_freq"],
        h["div_level"],
        h["agent"],
        h["agent_tel"],
        h["agent_addr"],
        h["firm"],
        h["cpa1"],
        h["cpa2"],
        h["eng_abbr"],
        h["eng_addr"],
        h["fax"],
        h["email"],
        h["url"],
        h["ir_contact"],
        h["ir_title"],
        h["ir_tel"],
        h["ir_email"],
        h["stake_url"],
    ]

    tpex_header = list(twse_header)
    tpex_header[14] = h["list_date_tpex"]
    return h, twse_header, tpex_header


def main():
    logger = _setup_logging()
    logger.info("=" * 60)
    logger.info("開始執行股票資料更新")
    logger.info("=" * 60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    logger.info(f"資料目錄: {data_dir}")

    header_keys, default_twse, default_tpex = _build_headers()
    twse_header = _latest_header(
        os.path.join(data_dir, "twse_*.csv"), default_twse, logger
    )
    tpex_header = _latest_header(
        os.path.join(data_dir, "tpex_*.csv"), default_tpex, logger
    )

    logger.info("開始下載 TWSE 資料...")
    twse_data = _request_json(TWSE_URL, logger)
    logger.info(f"TWSE 資料筆數: {len(twse_data)}")
    
    logger.info("開始下載 TPEX 資料...")
    tpex_data = _request_json(TPEX_URL, logger)
    logger.info(f"TPEX 資料筆數: {len(tpex_data)}")

    # Field mappings (API key names)
    twse_map = {
        header_keys["code"]: "\u516c\u53f8\u4ee3\u865f",
        header_keys["name"]: "\u516c\u53f8\u540d\u7a31",
        header_keys["abbr"]: "\u516c\u53f8\u7c21\u7a31",
        header_keys["industry"]: "\u7522\u696d\u5225",
        header_keys["foreign"]: "\u5916\u570b\u4f01\u696d\u8a3b\u518a\u5730\u570b",
        header_keys["address"]: "\u4f4f\u5740",
        header_keys["ubn"]: "\u71df\u5229\u4e8b\u696d\u7d71\u4e00\u7de8\u865f",
        header_keys["chair"]: "\u8463\u4e8b\u9577",
        header_keys["gm"]: "\u7e3d\u7d93\u7406",
        header_keys["spokes"]: "\u767c\u8a00\u4eba",
        header_keys["spokes_title"]: "\u767c\u8a00\u4eba\u8077\u7a31",
        header_keys["deputy"]: "\u4ee3\u7406\u767c\u8a00\u4eba",
        header_keys["tel"]: "\u7e3d\u6a5f\u96fb\u8a71",
        header_keys["inc_date"]: "\u6210\u7acb\u65e5\u671f",
        header_keys["list_date_twse"]: "\u4e0a\u5e02\u65e5\u671f",
        header_keys["par"]: "\u666e\u901a\u80a1\u6bcf\u80a1\u9762\u984d",
        header_keys["capital"]: "\u5be6\u6536\u8cc7\u672c\u984d",
        header_keys["issue_shares"]: "\u5df2\u767c\u884c\u666e\u901a\u80a1\u6578\u6216TDR\u539f\u80a1\u767c\u884c\u80a1\u6578",
        header_keys["private"]: "\u79c1\u52df\u80a1\u6578",
        header_keys["pref"]: "\u7279\u5225\u80a1",
        header_keys["fr_type"]: "\u7de8\u5236\u8ca1\u52d9\u5831\u8868\u985e\u578b",
        header_keys["agent"]: "\u80a1\u7968\u904e\u6236\u6a5f\u69cb",
        header_keys["agent_tel"]: "\u904e\u6236\u96fb\u8a71",
        header_keys["agent_addr"]: "\u904e\u6236\u5730\u5740",
        header_keys["firm"]: "\u7c3d\u8b49\u6703\u8a08\u5e2b\u4e8b\u52d9\u6240",
        header_keys["cpa1"]: "\u7c3d\u8b49\u6703\u8a08\u5e2b1",
        header_keys["cpa2"]: "\u7c3d\u8b49\u6703\u8a08\u5e2b2",
        header_keys["eng_abbr"]: "\u82f1\u6587\u7c21\u7a31",
        header_keys["eng_addr"]: "\u82f1\u6587\u901a\u8a0a\u5730\u5740",
        header_keys["fax"]: "\u50b3\u771f\u6a5f\u865f\u78bc",
        header_keys["email"]: "\u96fb\u5b50\u90f5\u4ef6\u4fe1\u7bb1",
        header_keys["url"]: "\u7db2\u5740",
    }

    tpex_map = {
        header_keys["code"]: "SecuritiesCompanyCode",
        header_keys["name"]: "CompanyName",
        header_keys["abbr"]: "CompanyAbbreviation",
        header_keys["industry"]: "SecuritiesIndustryCode",
        header_keys["foreign"]: "Registration",
        header_keys["address"]: "Address",
        header_keys["ubn"]: "UnifiedBusinessNo.",
        header_keys["chair"]: "Chairman",
        header_keys["gm"]: "GeneralManager",
        header_keys["spokes"]: "Spokesman",
        header_keys["spokes_title"]: "TitleOfSpokesman",
        header_keys["deputy"]: "DeputySpokesperson",
        header_keys["tel"]: "Telephone",
        header_keys["inc_date"]: "DateOfIncorporation",
        header_keys["list_date_tpex"]: "DateOfListing",
        header_keys["par"]: "ParValueOfCommonStock",
        header_keys["capital"]: "Paidin.Capital.NTDollars",
        header_keys["issue_shares"]: "IssueShares",
        header_keys["private"]: "PrivateStock.shares",
        header_keys["pref"]: "PreferredStock.shares",
        header_keys["fr_type"]: "PreparationOfFinancialReportType",
        header_keys["agent"]: "StockTransferAgent",
        header_keys["agent_tel"]: "StockTransferAgentTelephone",
        header_keys["agent_addr"]: "StockTransferAgentAddress",
        header_keys["firm"]: "AccountingFirm",
        header_keys["cpa1"]: "CPA.CharteredPublicAccountant.First",
        header_keys["cpa2"]: "CPA.CharteredPublicAccountant.Second",
        header_keys["eng_abbr"]: "Symbol",
        header_keys["fax"]: "Fax",
        header_keys["email"]: "EmailAddress",
        header_keys["url"]: "WebAddress",
    }

    stamp = date.today().strftime("%Y%m%d")
    twse_out = os.path.join(data_dir, "twse_%s.csv" % stamp)
    tpex_out = os.path.join(data_dir, "tpex_%s.csv" % stamp)

    logger.info(f"開始寫入 TWSE CSV: {twse_out}")
    with open(twse_out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(twse_header)
        for row in twse_data:
            out = []
            for col in twse_header:
                key = twse_map.get(col)
                out.append(row.get(key, "") if key else "")
            writer.writerow(out)
    logger.info(f"完成寫入 TWSE: {len(twse_data)} 筆資料")

    logger.info(f"開始寫入 TPEX CSV: {tpex_out}")
    with open(tpex_out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(tpex_header)
        for row in tpex_data:
            out = []
            for col in tpex_header:
                key = tpex_map.get(col)
                out.append(row.get(key, "") if key else "")
            writer.writerow(out)
    logger.info(f"完成寫入 TPEX: {len(tpex_data)} 筆資料")

    logger.info("=" * 60)
    logger.info("股票資料更新完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logging.error(f"更新失敗: {exc}", exc_info=True)
        sys.exit(1)