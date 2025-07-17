! ! ! NOT TESTED ! ! !

# `csgo.exe` – Real-Time RGB Integration for Team Fortress 2 via SteelSeries GameSense

## 🎯 Overview

`csgo.exe` is a lightweight background application that connects **Team Fortress 2** to **SteelSeries GG (GameSense Engine)** by mimicking **CS:GO**.  
It enables **real-time RGB lighting effects** that react to in-game events like health changes, damage, and more — using GameSense profiles that are whitelisted for CS:GO.

## ⚙️ How It Works

- The app runs **silently in the system tray** as a process named `csgo.exe`.
- It **registers itself as “CSGO”** with the GameSense Engine (so the CS:GO profile is activated).
- It **watches a TF2 log file** (`tf2_gamelog.txt`) in real-time for game events (e.g. damage received).
- When a matching event is detected, it **sends it immediately** to SteelSeries GG using GameSense's local HTTP API.

All of this happens in real-time — no polling or delay loops.

## ✅ Key Features

- ✅ Safe for VAC – **no memory access, no injection, no hacks**
- ✅ True real-time data processing
- ✅ Systray-only (no visible window)
- ✅ Auto-start compatible
- ✅ Easily extendable with more TF2 event triggers
- ✅ GitHub Actions support for building `csgo.exe`

## 🚀 Installation & Usage

### 1. **Download or Build**

You can either:
- Download a prebuilt `csgo.exe` from [GitHub Releases](#), or
- Clone this repo and build it yourself via Python or GitHub Actions.

### 2. **Install Dependencies (for manual use)**

```bash
pip install -r requirements.txt
```

Then build with:

```bash
pyinstaller --onefile --noconsole --icon=icon.ico --name csgo csgo.py
```

This will output `dist/csgo.exe`.

### 3. **Configure Team Fortress 2 Logging**

In TF2’s developer console, enable log output:

```
developer 1
con_logfile "tf2_gamelog.txt"
```

> 💡 This will write live gameplay events to a log file in your TF2 folder.

### 4. **Place `csgo.exe` Anywhere & Run**

Just double-click `csgo.exe`. It will:
- Register with SteelSeries GameSense
- Start monitoring TF2 logs
- Sit in your system tray quietly
- Send real-time RGB updates to SteelSeries devices

## 🧪 Example Use

When you take damage in TF2:

```log
Player hurt: health = 42
```

➡️ The app sends this value as a `HEALTH` event to GameSense → your keyboard/mouse lights up accordingly via the CS:GO profile.

## 📁 File Structure

```
csgo.py                 # Main application logic
icon.ico                # Tray icon (required for PyInstaller)
requirements.txt        # Python dependencies
.github/workflows/...   # GitHub Actions build pipeline
```

## 🛡️ VAC Safety

This project **only reads TF2’s log file**, which is externally generated and safe to access.  
It does **not** modify the game, memory, or use any cheat-like behavior. It is **100% VAC-safe**.
