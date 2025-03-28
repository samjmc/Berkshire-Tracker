# 📈 Berkshire Hathaway Stock Tracker

Get real-time updates when Berkshire Hathaway makes a move. This project tracks their latest 13F filings (institutional investment disclosures) using the SEC EDGAR API and presents them in a simple, interactive dashboard.

Launch the app here: https://berkshire-tracker.streamlit.app/ 

---

## Project Overview

This project helps you stay informed about the investment decisions of Berkshire Hathaway. It:

- Fetches Berkshire Hathaway’s latest 13F filings from the SEC
- Displays filing details in a user-friendly interface
- Can be extended to trigger alerts for stock buys/sells
- Demonstrates practical use of APIs, data wrangling, and Streamlit dashboard creation

---

## Features

-Live fetching of latest 13F filings
-Clean data parsing logic
-Streamlit web UI

---

## Tech Stack

- **Python** (Core language)
- **Requests** (API handling)
- **Streamlit** (Frontend dashboard)
- **SEC EDGAR API** (Data source)
- **Git** + **GitHub** (Version control)

---

## How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/your-username/berkshire-stock-tracker.git
cd berkshire-stock-tracker

# 2. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Streamlit app
streamlit run app.py


---



