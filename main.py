-                                                                                                                                                                                                                         import upstox_client
from upstox_client.rest import ApiException
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf      # For additional financial metrics

# Configuration
API_KEY = "your_upstox_api_key"
API_SECRET = "your_upstox_api_secret"
REDIRECT_URI = "your_redirect_uri"
ACCESS_TOKEN = "your_access_token"  # Obtain this after OAuth authentication

# Initialize Upstox API client
configuration = upstox_client.Configuration()
configuration.access_token = ACCESS_TOKEN
api_instance = upstox_client.HistoryApi(upstox_client.ApiClient(configuration))


# Function to fetch historical data
def fetch_historical_data(symbol, interval='1d', days_back=365):
    try:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)

        response = api_instance.get_historical_candle_data(
            instrument_key=symbol,  # e.g., "NSE_EQ|INE002A01018" for Reliance
            to_date=to_date.strftime('%Y-%m-%d'),
            from_date=from_date.strftime('%Y-%m-%d'),
            interval=interval,
            api_version='v2'
        )

        df = pd.DataFrame(response.data.candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

    except ApiException as e:
        print(f"Exception when calling HistoryApi: {e}")
        return None

# Function to calculate additional metrics
def calculate_metrics(df, symbol):
    # 1. Price Data
    latest_data = df.iloc[-1]
    price_data = {
        'open_price': latest_data['open'],
        'close_price': latest_data['close'],
        'high_price': latest_data['high'],
        'low_price': latest_data['low'],
        'adjusted_close': latest_data['close']  # Upstox doesn't provide adjusted close directly
    }
    # 2. Volume
    volume = latest_data['volume']

    # 3. Market Cap - Using yfinance for additional data
    stock = yf.Ticker(symbol.split('|')[1] if '|' in symbol else symbol)
    info = stock.info
    market_cap = info.get('marketCap', price_data['close_price'] * info.get('sharesOutstanding', 0))

    # 4. P/E Ratio
    pe_ratio = info.get('trailingPE', 0)

    # 5. EPS
    eps = info.get('trailingEps', 0)

    # 6. Dividends
    dividend_yield = info.get('dividendYield', 0) * 100
    dividend_payout_ratio = info.get('payoutRatio', 0) * 100

    # 7. Beta
    beta = info.get('beta', 0)

    # 8. 52-Week High/Low
    week_52_high = df['high'].max()
    week_52_low = df['low'].min()

    # 9. Moving Averages
    sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
    sma_200 = df['close'].rolling(window=200).mean().iloc[-1]
    ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]

    # 10. Volatility
    volatility = df['close'].pct_change().std() * np.sqrt(252)  # Annualized volatility

    # 11. RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]

    # 12. MACD
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_value = macd.iloc[-1] - signal.iloc[-1]

    # 13. P/B Ratio
    pb_ratio = info.get('priceToBook', 0)

    # 14. Debt-to-Equity Ratio
    de_ratio = info.get('debtToEquity', 0)

    # 15. Free Cash Flow
    fcf = info.get('freeCashflow', 0)

    # 16. Sector Performance (placeholder)
    sector = info.get('sector', 'N/A')
    return {
        'price_data': price_data,
        'volume': volume,
        'market_cap': market_cap,
        'pe_ratio': pe_ratio,
        'eps': eps,
        'dividend_yield': dividend_yield,
        'dividend_payout_ratio': dividend_payout_ratio,
        'beta': beta,
        '52_week_high': week_52_high,
        '52_week_low': week_52_low,
        'sma_50': sma_50,
        'sma_200': sma_200,
        'ema_50': ema_50,
        'volatility': volatility,
        'rsi': rsi,
        'macd': macd_value,
        'pb_ratio': pb_ratio,
        'de_ratio': de_ratio,
        'free_cash_flow': fcf,
        'sector': sector
    }

# Main function to process and save data
def process_and_save_data(symbol, filename='trade_data.csv'):
    # Fetch data
    df = fetch_historical_data(symbol)
    if df is None:
        return

    # Calculate metrics
    metrics = calculate_metrics(df, symbol)

    # Prepare data for saving
    data_to_save = {
        'Date': df['timestamp'].iloc[-1],
        'Symbol': symbol,
        **metrics['price_data'],
        'Volume': metrics['volume'],
        'Market_Cap': metrics['market_cap'],
        'PE_Ratio': metrics['pe_ratio'],
        'EPS': metrics['eps'],
        'Dividend_Yield': metrics['dividend_yield'],
        'Dividend_Payout_Ratio': metrics['dividend_payout_ratio'],
        'Beta': metrics['beta'],
        '52_Week_High': metrics['52_week_high'],
        '52_Week_Low': metrics['52_week_low'],
        'SMA_50': metrics['sma_50'],
        'SMA_200': metrics['sma_200'],
        'EMA_50': metrics['ema_50'],
        'Volatility': metrics['volatility'],
        'RSI': metrics['rsi'],
        'MACD': metrics['macd'],
        'PB_Ratio': metrics['pb_ratio'],
        'DE_Ratio': metrics['de_ratio'],
        'Free_Cash_Flow': metrics['free_cash_flow'],
        'Sector': metrics['sector']
    }

 # Save to CSV
    df_to_save = pd.DataFrame([data_to_save])
    df_to_save.to_csv(filename, mode='a', header=not pd.io.common.file_exists(filename), index=False)
    print(f"Data saved to {filename}")

# Example usage
symbol = "NSE_EQ|INE002A01018"  # Reliance Industries
process_and_save_data(symbol)