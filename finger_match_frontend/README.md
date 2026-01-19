# Finger Match Frontend (Expo)

This is a simple React Native (Expo) frontend for contactless-to-contact fingerprint matching.

## Setup

1. Install dependencies:
   ```sh
   npm install
   ```
2. Update the `BACKEND_URL` in App.js to point to your backend (e.g., http://192.168.x.x:5000/match).
3. Start the Expo app:
   ```sh
   npx expo start
   ```
4. Use Expo Go on your phone to scan the QR code and test the app.

## Features
- Import contactless finger image
- Import one or more contact-based fingerprint images
- Send images to backend for matching
- Display match result
