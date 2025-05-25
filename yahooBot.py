"""
台股KD指標分析器
"""
import sys
import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import time
import pandas as pd
import yfinance as yf

# 自定義模組導入
import kd_tools as kd
import potential_stars as ps
import logger
import emailService


@dataclass
class Config:
    """配置類別"""
    DEFAULT_KD_LIMITS: int = 20
    DEFAULT_DAYS: int = 7
    DATA_PERIOD_DAYS: int = 90
    BATCH_SIZE: int = 1000
    STOCK_FILE: str = "_stock.csv"
    REPORT_DIR: str = "reports"
    CONFIG_FILE: str = "config.json"
    POTENTIAL_STAR_THRESHOLD: float = 4.2
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5


class StockAnalyzer:
    """股票分析器主類"""
    
    def __init__(self, config: Config):
        self.config = config
        self.log = logger.get_log("log_config.yaml")
        self.report_dir = self._setup_report_directory()
        
    def _setup_report_directory(self) -> Path:
        """設置報告目錄"""
        report_path = Path.cwd() / self.config.REPORT_DIR
        try:
            report_path.mkdir(exist_ok=True)
            self.log.info("Report directory created/verified: %s", report_path)
            return report_path
        except OSError as e:
            self.log.exception("Failed to create report directory: %s", e)
            raise
    
    def load_stock_list(self) -> Dict[str, str]:
        """載入股票清單"""
        stock_file = Path(self.config.STOCK_FILE)
        
        if not stock_file.exists():
            self.log.error("Stock file %s not found", stock_file)
            raise FileNotFoundError(f"Stock file {stock_file} not found")
        
        try:
            with open(stock_file, "r", encoding="utf8") as f:
                companies = f.readlines()
            
            tickers_dict = {}
            for company_line in companies:
                company_data = company_line.strip()
                if company_data and ',' in company_data:
                    parts = company_data.split(',')
                    if len(parts) >= 3:
                        ticker_id = parts[0]
                        tickers_dict[ticker_id] = company_data
                    
            self.log.info("Loaded %d stocks from %s", len(tickers_dict), stock_file)
            return tickers_dict
            
        except (IOError, UnicodeDecodeError) as e:
            self.log.exception("Error reading stock file: %s", e)
            raise
    
    def download_stock_data(self, tickers: List[str], retries: int = 0) -> Optional[pd.DataFrame]:
        """下載股票數據，支援重試機制"""
        try:
            self.log.info("Downloading data for %d stocks...", len(tickers))
            df = yf.download(
                tickers, 
                group_by="ticker", 
                period="1mo",
                progress=False
            )
            
            if df.empty:
                self.log.warning("Downloaded data is empty")
                return None
                
            self.log.info("Stock data downloaded successfully")
            return df
            
        except Exception as e:
            self.log.error("Error downloading stock data (attempt %d): %s", retries + 1, e)
            
            if retries < self.config.MAX_RETRIES:
                self.log.info("Retrying in %d seconds...", self.config.RETRY_DELAY)
                time.sleep(self.config.RETRY_DELAY)
                return self.download_stock_data(tickers, retries + 1)
            else:
                self.log.error("Max retries reached. Download failed.")
                return None
    
    def process_batch(self, batch_tickers: List[str], tickers_dict: Dict[str, str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """處理單一批次的股票數據"""
        batch_kd_df = pd.DataFrame()
        batch_stars_df = pd.DataFrame()
        
        # 下載批次數據
        df = self.download_stock_data(batch_tickers)
        if df is None or df.empty:
            return batch_kd_df, batch_stars_df
        
        # 處理多股票數據格式
        if len(batch_tickers) == 1:
            # 單一股票的情況
            ticker = batch_tickers[0]
            processed_data = {ticker: df}
        else:
            # 多股票的情況
            processed_data = {idx: gp.T for idx, gp in df.T.groupby(level=0)}
        
        # 處理每支股票
        for ticker_id, stock_data in processed_data.items():
            try:
                kd_result, stars_result = self._process_single_stock(
                    ticker_id, stock_data, tickers_dict
                )
                
                if kd_result is not None and not kd_result.empty:
                    batch_kd_df = pd.concat([batch_kd_df, kd_result], ignore_index=True)
                
                if stars_result is not None and not stars_result.empty:
                    batch_stars_df = pd.concat([batch_stars_df, stars_result], ignore_index=True)
                    
            except Exception as e:
                self.log.error("Error processing stock %s: %s", ticker_id, e)
                continue
        
        return batch_kd_df, batch_stars_df
    
    def _process_single_stock(self, ticker_id: str, stock_data: pd.DataFrame, 
                            tickers_dict: Dict[str, str]) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """處理單支股票的數據"""
        
        # 獲取股票基本資訊
        ticker_info = tickers_dict.get(ticker_id)
        if not ticker_info:
            return None, None
        
        try:
            parts = ticker_info.split(',')
            ticker_name = parts[1] if len(parts) > 1 else "Unknown"
            ticker_industry = parts[2].replace("\n", "") if len(parts) > 2 else "Unknown"
        except IndexError:
            self.log.warning("Invalid ticker info format for %s", ticker_id)
            return None, None
        
        # 標準化欄位名稱
        if 'Adj Close' in stock_data.columns.get_level_values(1) if hasattr(stock_data.columns, 'get_level_values') else stock_data.columns:
            stock_data.columns = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
        else:
            stock_data.columns = ["Open", "High", "Low", "Close", "Volume"]
        
        # 添加股票資訊
        stock_data['id'] = ticker_id
        stock_data['name'] = ticker_name
        stock_data['industry'] = ticker_industry
        
        # 計算KD指標
        kd_result = self._calculate_kd_analysis(stock_data)
        
        # 尋找潛在飆股
        stars_result = self._find_potential_stars(stock_data)
        
        return kd_result, stars_result
    
    def _calculate_kd_analysis(self, stock_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """計算KD分析"""
        try:
            df_kd = kd.calculate_kd(stock_data)
            if df_kd is None or df_kd.empty:
                return None
            
            kd_under_level = kd.filter_data_days(
                df_kd, 
                days_in_advance=self.config.DEFAULT_DAYS, 
                d_num=self.config.DEFAULT_KD_LIMITS
            )
            
            return kd_under_level[["id", "name", "industry", "Close", "K", "D", "Volume"]]
            
        except Exception as e:
            self.log.error("Error in KD calculation: %s", e)
            return None
    
    def _find_potential_stars(self, stock_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """尋找潛在飆股"""
        try:
            recent_data = stock_data.tail(2)
            if len(recent_data) < 2:
                return None
            
            prev_day_data = recent_data.iloc[0]
            current_day_data = recent_data.iloc[1]
            
            if ps.is_potential_star(
                prev_day_data, 
                current_day_data, 
                self.log, 
                self.config.POTENTIAL_STAR_THRESHOLD
            ):
                return recent_data[["id", "name", "industry", "Close", "K", "D", "Volume"]]
            
            return None
            
        except Exception as e:
            self.log.error("Error in potential stars analysis: %s", e)
            return None
    
    def chunks(self, lst: List, n: int):
        """將列表分割成指定大小的批次"""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    def analyze_stocks(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """主要分析函數"""
        # 載入股票清單
        tickers_dict = self.load_stock_list()
        all_tickers = list(tickers_dict.keys())
        
        # 初始化結果DataFrame
        total_kd_df = pd.DataFrame()
        total_stars_df = pd.DataFrame()
        
        # 分批處理股票
        ticker_batches = list(self.chunks(all_tickers, self.config.BATCH_SIZE))
        
        self.log.info("Processing %d stocks in %d batches", len(all_tickers), len(ticker_batches))
        
        for i, batch in enumerate(ticker_batches):
            progress = f"[{i+1}/{len(ticker_batches)}]"
            print(f"{progress} Processing batch {i+1} ({len(batch)} stocks)...")
            self.log.info("Processing batch %d/%d (%d stocks)", i+1, len(ticker_batches), len(batch))
            
            try:
                batch_kd_df, batch_stars_df = self.process_batch(batch, tickers_dict)
                
                if not batch_kd_df.empty:
                    total_kd_df = pd.concat([total_kd_df, batch_kd_df], ignore_index=True)
                
                if not batch_stars_df.empty:
                    total_stars_df = pd.concat([total_stars_df, batch_stars_df], ignore_index=True)
                
                # 批次間暫停，避免API限制
                if i < len(ticker_batches) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                self.log.error("Error processing batch %d: %s", i+1, e)
                continue
        
        return total_kd_df, total_stars_df
    
    def save_results(self, kd_df: pd.DataFrame, stars_df: pd.DataFrame) -> List[str]:
        """保存分析結果"""
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        attachments = []
        
        # 生成檔案名稱
        kd_excel_filename = f'kd{self.config.DEFAULT_KD_LIMITS}_TW_{current_date}.xlsx'
        kd_csv_filename = f'kd{self.config.DEFAULT_KD_LIMITS}_TW_{current_date}.csv'
        stars_excel_filename = f'stars_TW_{current_date}.xlsx'
        stars_csv_filename = f'stars_TW_{current_date}.csv'
        
        # 保存KD結果
        if not kd_df.empty:
            # 清理股票代號格式
            kd_df["id"] = kd_df["id"].str.replace(r"\.TWO$|\.TW$", "", regex=True)
            
            # 保存檔案
            kd_excel_path = self.report_dir / kd_excel_filename
            kd_csv_path = self.report_dir / kd_csv_filename
            
            kd_df.to_csv(kd_csv_path, sep=",", index=True, header=True, encoding='utf-8-sig')
            kd_df.to_excel(kd_excel_path, index=True, engine="openpyxl")
            
            attachments.append(str(kd_excel_path))
            self.log.info("KD results saved: %s", kd_excel_path)
        
        # 保存潛在飆股結果
        if not stars_df.empty:
            # 清理股票代號格式
            stars_df["id"] = stars_df["id"].str.replace(r"\.TWO$|\.TW$", "", regex=True)
            
            # 保存檔案
            stars_excel_path = self.report_dir / stars_excel_filename
            stars_csv_path = self.report_dir / stars_csv_filename
            
            stars_df.to_csv(stars_csv_path, sep=",", index=True, header=True, encoding='utf-8-sig')
            stars_df.to_excel(stars_excel_path, index=True, engine="openpyxl")
            
            attachments.append(str(stars_excel_path))
            self.log.info("Potential stars results saved: %s", stars_excel_path)
        
        return attachments
    
    def send_email_report(self, attachments: List[str]) -> None:
        """發送email報告"""
        if not attachments:
            self.log.info("No attachments to send")
            return
        
        try:
            emailService.send_mail(log=self.log, attaches=attachments)
            self.log.info("Email sent successfully")
        except Exception as e:
            self.log.exception("Failed to send email: %s", e)
    
    def run_analysis(self) -> None:
        """執行完整分析流程"""
        try:
            self.log.info("Starting stock analysis...")
            start_time = time.time()
            
            # 執行分析
            kd_df, stars_df = self.analyze_stocks()
            
            # 保存結果
            attachments = self.save_results(kd_df, stars_df)
            
            # 發送email
            self.send_email_report(attachments)
            
            # 記錄統計資訊
            elapsed_time = time.time() - start_time
            self.log.info("Analysis completed successfully in %.2f seconds", elapsed_time)
            self.log.info("Found %d stocks with low KD values", len(kd_df))
            self.log.info("Found %d potential star stocks", len(stars_df))
            
        except Exception as e:
            self.log.exception("Analysis failed: %s", e)
            raise


def load_config() -> Config:
    """載入配置文件，如果不存在則使用預設值"""
    config = Config()
    config_file = Path(config.CONFIG_FILE)
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新配置值
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            print("Configuration loaded from %s", config_file)
        except Exception as e:
            print("Error loading config file: %s, using defaults", e)
    else:
        # 創建預設配置文件
        default_config = {
            "DEFAULT_KD_LIMITS": config.DEFAULT_KD_LIMITS,
            "DEFAULT_DAYS": config.DEFAULT_DAYS,
            "DATA_PERIOD_DAYS": config.DATA_PERIOD_DAYS,
            "BATCH_SIZE": config.BATCH_SIZE,
            "POTENTIAL_STAR_THRESHOLD": config.POTENTIAL_STAR_THRESHOLD,
            "MAX_RETRIES": config.MAX_RETRIES,
            "RETRY_DELAY": config.RETRY_DELAY
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print("Default configuration file created: %s", config_file)
        except Exception as e:
            print("Could not create config file: %s", e)
    
    return config


def main():
    """主函數"""
    try:
        # 載入配置
        config = load_config()
        
        # 創建分析器並執行分析
        analyzer = StockAnalyzer(config)
        analyzer.run_analysis()
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print("Critical error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()