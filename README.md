# day-map
CIS 4120 - Penn Campus Event Planner

Run these from the `frontend` folder.

```bash
cd frontend
npm install
npx expo login
```

Sign in with the same Expo account you use in Expo Go.

## Phone (Expo Go)

1. Install Expo Go from the App Store or Play Store.
2. Sign in to Expo Go.
3. On the Mac, from `frontend`, run `npx expo login` and sign in with that same account.
4. Connect the phone and the Mac to the same Wi-Fi.
5. Run `npx expo start`.
6. Scan the QR code. iPhone: Camera app. Android: the scanner inside Expo Go.

## Mac (Xcode simulator)

1. Install Xcode from the App Store and open it once so it can finish setup.
2. Run `npx expo start`.
3. Press `i` to open the iOS Simulator.

If Xcode is installed and the simulator still will not start, run:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```
