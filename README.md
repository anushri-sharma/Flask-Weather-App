# Flask Weather App

Search any city and see current conditions plus a 5-day forecast.
Uses the free [Open-Meteo](https://open-meteo.com) API, so no API key is needed.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Structure

- `app.py` – Flask routes: `/` (page) and `/api/weather?city=...&units=metric|imperial` (JSON)
- `templates/index.html` – UI; the colour theme changes with the current sky
