# Need for Speed Most Wanted (2005, PC) — Port


### Android downloads

| APK | 64 Bit |
|---|---|
| [Download](https://github.com/ArieSR91/nfsmwpc-port-mobile/releases/download/v0.1.13/app-debug.apk) | v0.1.13 |

Android 10+ and Vulkan 1.1+. Both APKs use the same package and signing key;
install the architecture supported by your device. Original game data is required.
Audio, pacing and validation details: [runtime follow-up](docs/AUDIO_FRAME_PACING.md).

### What's new
- Add 2 new button (lookback and blacklist)
- Add slider to set button opacity

### Playing on Android

1. Install the APK for your architecture (arm64 recommended).
2. Copy your PC installation into `Internal storage/nfsmw` so that `nfsmw/Speed.exe` exists
   next to `GLOBAL`, `TRACKS`, `CARS`, `FRONTEND`, `LANGUAGES`, `SOUND`, `MOVIES` and `NIS`.
   Add `d3dx9_26.dll` (DirectX runtime, from your Windows `SysWOW64`) and, for LAN hosting,
   `server.dll` and `server.cfg` from the game.
3. Open the launcher, pick your language with the flags (Español, English, Português),
   grant file access and press **PLAY**.

The launcher sets the internal resolution, FPS limit, proportional widescreen HUD, minimap position
(top-left by default, so the steering thumb does not cover it), CPU/GPU latency, compressed texture
mode, Vulkan driver (system or a custom Turnip ZIP) and the Online server. In game, the on-screen
controls can be moved, resized and switched to classic, Xbox or PlayStation layouts, or replaced by
tilt steering or a Bluetooth/USB gamepad.

Android runtime fixes and current verification limits: [bring-up notes](docs/ANDROID_BRINGUP.md).
