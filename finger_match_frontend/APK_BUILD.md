## Build an Android APK (for sharing with manager)

### Prerequisites
- **Node** installed
- **Expo CLI** available via `npx`
- An **Expo account** (for EAS builds)

### 1) Install dependencies

```bash
cd /Users/sakina/Downloads/deployment/finger_match_frontend
npm install
```

### 2) Ensure Android allows HTTP (already configured)
This project uses an HTTPS backend URL (`https://finger-match-backend.onrender.com`), so it is secure.

This is already set in `app.json`:
- `expo.android.usesCleartextTraffic = true`

### 3) Recommended: Build a shareable APK using EAS (easiest)

```bash
cd /Users/sakina/Downloads/deployment/finger_match_frontend
npx eas login
npx eas build:configure
npx eas build --platform android --profile preview
```

After build finishes, EAS will print a link. Download the APK from that link and share it.

### 4) Optional: Build locally (requires Android Studio + SDK)

```bash
cd /Users/sakina/Downloads/deployment/finger_match_frontend
npx expo prebuild --platform android
cd android
./gradlew assembleRelease
```

APK output (typical):
- `android/app/build/outputs/apk/release/app-release.apk`

