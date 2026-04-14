# App – King Domino Expo-app

React Native (Expo) app til at fotografere et King Domino-bræt og beregne scoren via backend-API'et.

## Skærme

1. **Startside** – Hero-billede og "Beregn point"-knap
2. **Kamera** – Tag et foto med kameraet eller vælg fra biblioteket
3. **Resultat** – Vis score, kroner, clusters og session-log

## Opsætning

Sørg for at Node.js (≥ 18) og Expo CLI er installeret:

```bash
npm install --global expo-cli
```

Installer afhængigheder:

```bash
cd app
npm install
```

## Start appen

```bash
cd app
npx expo start
```

Scan QR-koden med Expo Go-appen på din telefon.

## Konfiguration

Sæt backend-adressen med en miljøvariabel (fx din computers lokale IP):

```bash
EXPO_PUBLIC_API_URL=http://192.168.1.42:8000 npx expo start
```

Standardværdien er `http://localhost:8000`.

## Krav

- Expo Go på Android eller iOS
- Backend kørende på samme netværk
