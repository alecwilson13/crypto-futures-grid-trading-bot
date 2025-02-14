# Phemex Grid Trading Bot

## Overview
This is a Python-based GUI application for implementing grid trading strategies on Phemex futures contracts. The bot allows users to create automated grid trading strategies with features like configurable grid levels, leverage, and market direction.

## Features
- 🔒 Secure API Key Management
- 📊 Real-time Account Overview
- 📈 Grid Trading Configuration
- 🤖 Automated Order Creation
- 📝 Detailed Logging
- 💹 Long and Short Trading Strategies

## Prerequisites
- Python 3.8+
- Required Libraries:
  - tkinter
  - ccxt
  - pandas

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/phemex-grid-trading-bot.git
cd phemex-grid-trading-bot
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Configuration Requirements
- Phemex API Key
- API Secret
- Futures Trading Permissions Enabled

## Usage Instructions

### 1. Connect to Phemex
1. Enter your Phemex API Key
2. Enter your API Secret
3. Click "Connect"

### 2. Configure Grid Trading
- Select Market (BTC/USD, ETH/USD, SOL/USD)
- Set Lower Price
- Set Upper Price
- Configure Number of Grid Levels
- Set Total Investment
- Choose Leverage
- Select Trading Direction (Long/Short)

### 3. Trading Options
- **Preview Grid**: Simulate grid levels without executing trades
- **Create Grid Bot**: Deploy your grid trading strategy
- **Close All Positions**: Immediately exit all active positions

## Risk Management
⚠️ **IMPORTANT**: 
- Grid trading involves significant financial risk
- Always start with small investments
- Thoroughly understand the strategy before large-scale deployment
- This is an experimental tool - use at your own risk

## Security Notes
- API keys are stored locally in `grid_trading_config.json`
- Secret is not permanently stored
- Ensure your API key has appropriate trading permissions

## Troubleshooting
- Verify API Key permissions
- Check network connectivity
- Ensure sufficient account balance
- Review error logs in the application

## Supported Markets
- BTC/USD Futures
- ETH/USD Futures
- SOL/USD Futures

## Disclaimer
This software is provided "as is" without warranty of any kind. Trading cryptocurrencies carries high risk. The authors are not responsible for any financial losses.

## Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## License
[Specify your license, e.g., MIT]

## Contact
[Your Contact Information]

## Acknowledgments
- [ccxt Library](https://github.com/ccxt/ccxt)
- [Phemex API](https://phemex.com/api-trading)

Would you like me to also create a `requirements.txt` file to accompany this README?
