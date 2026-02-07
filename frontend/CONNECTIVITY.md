# Fix: "Cannot reach backend" in Chrome and Android emulator

The server works when you `curl` it, but the Flutter app still can't connect. Follow these steps **in order**.

---

## Step 1: Restart the backend (so CORS is active)

From the **project root** (`tutorApp`):

```bash
docker compose down
docker compose up -d
```

Wait a few seconds, then check:

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/v1/content/quick-notes
```

You should see JSON. If not, fix the backend first (DB, .env, port 8000).

---

## Step 2: Chrome (Flutter web)

1. Backend is running and returns results (Step 1).
2. **Restart the Flutter web app** (stop and run again):
   ```bash
   cd frontend
   flutter run -d chrome
   ```
3. Open **Quick Notes** in the app.

If it still fails in Chrome:

- Open **Chrome DevTools** (F12) → **Network** tab.
- Trigger Quick Notes again.
- Click the request to `quick-notes`. Check:
  - **Status**: 0 or (failed) often means CORS or connection blocked.
  - **Response headers** (if any): look for `Access-Control-Allow-Origin`.

If there is no `Access-Control-Allow-Origin` in the response, the backend didn’t send CORS headers (old process still running, or CORS not applied). Stop all backend processes and start again with `docker compose up -d`.

---

## Step 3: Android emulator

**Option A – adb reverse (recommended, same URL as Chrome)**  
Run this **once per emulator boot** so the emulator’s port 8000 is your Mac’s 8000:

```bash
adb reverse tcp:8000 tcp:8000
```

Then run the app **with the same base URL as Chrome** (so both use localhost):

```bash
cd frontend
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

Use this when running on the **Android device** in the run selector; the app will use `http://localhost:8000` and adb will forward it to your Mac.

**Option B – use your Mac’s IP**  
If Option A still fails:

1. Get your Mac’s IP (it can change when you switch Wi‑Fi):
   ```bash
   ipconfig getifaddr en0
   ```
   (Usually Wi‑Fi; use `en1` if you’re on Ethernet, or `ifconfig | grep "inet " | grep -v 127.0.0.1` to see all.)
2. Run with that IP, or **use it automatically** so you don’t need to look it up each time:
   ```bash
   flutter run --dart-define=API_BASE_URL=http://$(ipconfig getifaddr en0):8000
   ```
   Backend must be listening on `0.0.0.0:8000` (Docker does this).

---

## Step 4: If nothing works – run the backend on the Mac (no Docker)

To rule out Docker networking:

```bash
cd tutorApp/backend
# use your venv if you have one
pip install -r requirements.txt
# set .env or export DB vars, then:
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then:

- **Chrome:** `flutter run -d chrome` and open Quick Notes (app uses `http://localhost:8000`).
- **Android:** run `adb reverse tcp:8000 tcp:8000`, then run the app with `http://localhost:8000` for Android (see below) or use your Mac IP as in Step 3.

---

## Summary

| Where        | App calls            | What you must do |
|-------------|----------------------|-------------------|
| **Chrome**  | `http://localhost:8000` | Backend running; CORS enabled (restart backend after adding CORS). |
| **Android** | `http://10.0.2.2:8000`  | Backend running; or use `adb reverse tcp:8000 tcp:8000` and/or `API_BASE_URL=http://YOUR_MAC_IP:8000`. |
