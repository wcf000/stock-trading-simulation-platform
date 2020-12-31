# Stock Trading Simulation Platform

A web-based platform that allows users to simulate buying and selling stocks with virtual money. Built with Flask, this application provides a safe environment to practice trading strategies without risking real money.

## Features

- **User Authentication**: Register an account, log in, and change passwords securely
- **Portfolio Management**: View your current holdings and cash balance
- **Real-time Quotes**: Look up real-time stock prices using IEX API
- **Trading**: Buy and sell stocks with virtual money
- **Transaction History**: Track all your past transactions
- **Security**: Password hashing and session management for secure user experience

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with CS50 SQL library
- **Frontend**: HTML, CSS, Bootstrap 4.1
- **APIs**: IEX Cloud for real-time stock data

## Setup and Installation

1. Clone the repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set your IEX API key as an environment variable:
   ```
   export API_KEY=your_api_key
   ```
   (On Windows: `set API_KEY=your_api_key`)
4. Run the application:
   ```
   flask run
   ```

## Usage

1. Register for an account
2. Use the "Quote" feature to look up stock prices
3. Buy stocks with your initial cash balance
4. Track your portfolio performance
5. Sell stocks when needed
6. Check your transaction history

## Database Schema

The application uses the following main tables:
- `users`: Stores user accounts and cash balances
- `current`: Tracks users' current stock holdings
- `record`: Stores all transaction records

## Notes

- The application uses a SQLite database named `finance.db` (not included in the repository)
- Each new user starts with $10,000 in virtual cash
- Stock data is provided by IEX Cloud, which requires an API key

## License

This project is part of a learning exercise in CS50 done in 2020 and is intended for educational purposes.

## Acknowledgements

- Data provided by [IEX Cloud](https://iextrading.com/developer)
- Built with [Flask](https://flask.palletsprojects.com/)
- Frontend styled with [Bootstrap](https://getbootstrap.com/)