# PropVault — +EV Engine

Real-time +EV bet finder. Pulls Pinnacle (sharp) and Novig lines from
The Odds API, strips vig from Pinnacle to derive fair probabilities,
and surfaces any Novig line where you have a positive edge.

## How it works

1. Fetches MLB + NBA odds from The Odds API for Pinnacle and Novig
2. Strips the vig from Pinnacle's paired lines (additive devig)
3. Calculates fair probability for each side
4. Compares against Novig: if `EV% = (fair_prob × decimal_odds) − 1 > 0`, it's +EV
5. Returns all bets above the minimum threshold, sorted by EV descending

## Run locally

```bash
# Install dependencies
pip install -r requirements.txt

# Add your API key
mkdir -p .streamlit
echo 'ODDS_API_KEY = "your_key_here"' > .streamlit/secrets.toml

# Run
streamlit run app.py
```

## Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to share.streamlit.io → New app
3. Select your repo and set **Main file path** to `app.py`
4. Go to **Settings → Secrets** and add:
   ```
   ODDS_API_KEY = "your_key_here"
   ```
5. Deploy — done

## File structure

```
propvault/
├── app.py              # Streamlit UI
├── ev_engine.py        # EV math + Odds API fetching
├── requirements.txt    # Dependencies
├── .gitignore          # Keeps secrets out of git
├── .streamlit/
│   └── secrets.toml.example   # Secret key template
└── README.md
```

## Configuration

| Setting | File | Default |
|---|---|---|
| Min EV threshold | `ev_engine.py` → `MIN_EV` | 1.5% |
| Sports to scan | `ev_engine.py` → `SPORTS` | MLB, NBA |
| Markets to scan | `ev_engine.py` → `MARKETS` | Moneyline, Spread, Total |
| Sharp book | `ev_engine.py` → `SHARP_BOOK` | pinnacle |
| Target book | `ev_engine.py` → `TARGET_BOOK` | novig |
