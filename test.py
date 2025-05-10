import yfinance as yf

ticker = yf.Ticker("2330.TW")
hist = ticker.history(period="7d")
print(hist)
