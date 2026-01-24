# Apollo13 - Taiwan Stock Market KD Analyzer

A Python-based automated stock analysis tool that identifies bullish trading signals in Taiwan's stock market using KD (Stochastic) indicators and volume analysis.

## Features

- **KD Indicator Analysis**: Calculates Stochastic oscillator (K and D lines) for technical analysis
- **Potential Star Detection**: Identifies stocks with bullish price action and volume spikes
- **Automated Reporting**: Generates CSV reports and sends via email
- **Retry Logic**: Built-in retry mechanism for network failures
- **Containerized**: Docker support for cloud deployment
- **Configurable**: YAML and JSON configuration for easy customization

## Project Structure

```
Apollo13/
├── yahooBot.py              # Main orchestrator - downloads and analyzes stocks
├── kd_tools.py              # KD indicator calculations and filtering
├── potential_stars.py       # Bullish signal detection logic
├── emailService.py          # Email delivery with attachments
├── logger.py                # Logging factory
├── transfer_data.py         # Data transfer utilities
├── config.json              # Application configuration
├── log_config.yaml          # Logging configuration
├── gmail_config.yaml        # Email configuration (sensitive)
├── requirements             # Python dependencies
├── Dockerfile               # Docker container definition
└── reports/                 # Generated CSV reports
```

## Installation

### Prerequisites
- Python 3.8+
- pip or conda

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd Apollo13
```

2. **Create virtual environment (optional but recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements
```

4. **Configure Gmail (for email reports)**
Edit `gmail_config.yaml`:
```yaml
email:
  sender_email: your_email@gmail.com
  sender_password: your_app_password  # Use App Password for Gmail
  receiver_emails:
    - recipient@example.com
  subject: "Taiwan Stock KD Analysis Report"
  body: "See attached for today's stock analysis"
```

## Configuration

### config.json
```json
{
    "DEFAULT_KD_LIMITS": 20,        # KD threshold for bullish signals
    "DEFAULT_DAYS": 7,              # Analysis lookback period (days)
    "DATA_PERIOD_DAYS": 90,         # Historical data fetch period
    "BATCH_SIZE": 1000,             # Stocks per batch
    "POTENTIAL_STAR_THRESHOLD": 4.2, # Unused (for future enhancement)
    "MAX_RETRIES": 3,               # Network retry attempts
    "RETRY_DELAY": 5                # Delay between retries (seconds)
}
```

### Stock List Format (_stock.csv)
```
2330,TSMC,Semiconductors
2454,MediaTek,Semiconductors
3008,Largan,Optics
```

## Usage

### Command Line
```bash
python yahooBot.py
```

### Update TWSE/TPEX Listings
```bash
python update_listings.py
```

This writes new files to `data/` using today's date in the filename:
- `twse_YYYYMMDD.csv`
- `tpex_YYYYMMDD.csv`

### Cron Job (Linux/Mac)
```bash
# Run daily at 2:00 PM
0 14 * * * cd /path/to/Apollo13 && python yahooBot.py >> run.log 2>&1
```

### Schedule Update (Linux/Mac)
```bash
# Run weekdays at 8:30 AM
30 8 * * 1-5 cd /path/to/Apollo13 && python update_listings.py >> run.log 2>&1
```

### Schedule Update (Windows Task Scheduler)
```powershell
# Run weekdays at 08:30
schtasks /Create /SC WEEKLY /D MON,TUE,WED,THU,FRI /TN "Apollo13 Update Listings" `
  /TR "C:\Path\To\Python\python.exe C:\Path\To\Apollo13\update_listings.py" /ST 08:30
```

### Docker
```bash
docker build -t apollo13 .
docker run -v $(pwd)/reports:/app/reports apollo13
```

## Technical Details

### KD Indicator
- **K Line**: 100 × (Close - Low9) / (High9 - Low9), smoothed with EMA(1/3)
- **D Line**: EMA(K, 1/3)
- **Signal**: K and D below 20 = oversold (potential buy)

### Potential Star Logic
A stock is flagged as a "potential star" when:
1. **Price Increase**: Closing price > previous day's close
2. **Volume Spike**: Current volume > 3x previous day's volume

## Dependencies

- `pandas`: Data manipulation
- `yfinance`: Financial data fetching
- `numpy`: Numerical computing
- `pyaml`: YAML parsing
- `beautifulsoup4`: Web scraping support
- `peewee`: ORM for data persistence

## Troubleshooting

### Email Not Sending
- Verify Gmail app password (not regular password)
- Check `gmail_config.yaml` file permissions
- Review logs in `run.log`

### No Data Downloaded
- Verify internet connection
- Check ticker symbols in `_stock.csv`
- Review `yfinance` availability

### Missing Reports
- Ensure `reports/` directory exists
- Check write permissions
- Verify stock file is not empty

## Future Enhancements

- [ ] Database storage instead of CSV
- [ ] Web dashboard for visualization
- [ ] Additional technical indicators (MACD, RSI)
- [ ] Notification alerts (SMS, Slack)
- [ ] Performance backtesting
- [ ] Machine learning predictions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with clear commit messages
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Notes

- Taiwan stock symbols use `.TW` suffix (e.g., `2330.TW`)
- Reports are timestamped in YYYY-MM-DD format
- Sensitive credentials should use environment variables
