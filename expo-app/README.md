# King Domino Analyzer – Expo App

A React Native (Expo) mobile app for calculating King Domino scores.

## Screens

| Screen | Description |
|--------|-------------|
| **Home** | Hero image + "Calculate" button |
| **Camera** | Live camera with 5×5 grid overlay; photo or library import |
| **Results** | Score banner, board grid, legend, cluster breakdown |

## Setup

```bash
cd expo-app
npm install
```

## Running

```bash
npx expo start
```

Scan the QR code with the **Expo Go** app (iOS/Android).

## Backend URL

Open `screens/CameraScreen.js` and update `API_BASE_URL` to point to the machine running the FastAPI backend:

```js
const API_BASE_URL = 'http://<your-local-ip>:8000';
```

> **Tip:** On Android Emulator use `http://10.0.2.2:8000`.  
> On iOS Simulator use `http://localhost:8000`.
