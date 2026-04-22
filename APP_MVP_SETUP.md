# King Domino MVP App Setup

## 1) Backend (FastAPI)

Fra projektroden:

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Test health:

```powershell
curl http://127.0.0.1:8000/health
```

## 2) Expo app

Gå til app-mappen:

```powershell
cd app
npm install
npm run start
```

## 3) Sæt backend-URL i app

I `app/App.js` skal du ændre:

```js
const API_BASE_URL = 'http://127.0.0.1:8000';
```

Til din PC's lokale IP hvis du tester på telefon på samme netværk, fx:

```js
const API_BASE_URL = 'http://192.168.1.17:8000';
```

## 4) Hvad MVP'en indeholder

- Hero-billede på start/loading: `app/assets/hero.png`
- Kamera-flow i app
- API-kald til backend (`/analyze`)
- Resultatvisning (score, crowns, clusters)
- Session-log i app-memory

## 5) Noter

- Backend normaliserer inputbilledet til 500x500 for at matche nuværende pipeline.
- Nu er kun kamera-flow med i MVP (ingen upload-galleri endnu).
