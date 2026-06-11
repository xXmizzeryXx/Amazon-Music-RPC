# Amazon Music Discord Rich Presence

Displays your currently playing Amazon Music track on your Discord profile in real time — including song title, artist, album, and a live progress bar showing how far into the song you are.

<img src="logo.png" alt="Amazon Music Discord Rich Presence" width="128"/>

---

## How it works

This script uses the **Windows System Media Transport Controls (SMTC)** API — the same system that powers your taskbar "Now Playing" widget and media keys (⏯ ⏮ ⏭). Every 3 seconds it reads the current track from Amazon Music and pushes it to Discord via the local Rich Presence RPC socket that Discord exposes on every machine running the desktop app.

No screen scraping, no browser extensions, no Amazon account credentials required.

---

## Requirements

- **Windows 10 version 1903+ or Windows 11**
- **Python 3.9 or newer** — download at https://python.org
- **Amazon Music desktop app** — the browser player does not work
- **Discord desktop app**

---

## Installation

### Step 1 — Download the script

Save `amazon_music_rpc.py` somewhere you'll remember, for example:

```
C:\Users\YourName\amazon-music-rpc\amazon_music_rpc.py
```

### Step 2 — Install Python dependencies

Open a terminal (press `Win + R`, type `cmd`, hit Enter) and run:

```bash
pip install winsdk pypresence psutil
```

`winsdk` compiles C++ bindings during install and can take **5–10 minutes** the first time. This is normal — just let it run.

### Step 3 — Create a Discord Application

This is how Discord knows what name and icon to display on your profile.

1. Go to https://discord.com/developers/applications
2. Click **New Application** in the top right
3. Give it a name — this is what shows on your profile, so use something like `Amazon Music`
4. Click **Create**
5. You'll land on the **General Information** page — copy the **Application ID** (a long number like `1234567890123456789`)

You do not need to configure anything else on this page.

### Step 4 — Add a logo (optional but recommended)

If you want your Amazon Music logo to appear as the large icon on your profile card:

1. In your Discord application, go to **Rich Presence → Art Assets** in the left sidebar
2. Click **Add Image(s)** and upload your logo file
3. Set the key name to exactly `amazon_music_logo`
4. Click **Save Changes**

The image must be at least 512×512px. PNG with a transparent background works best.

### Step 5 — Configure the script

Open `amazon_music_rpc.py` in any text editor (Notepad works fine) and replace the placeholder on this line near the top:

```python
DISCORD_CLIENT_ID = "YOUR_DISCORD_CLIENT_ID_HERE"
```

with your actual Application ID:

```python
DISCORD_CLIENT_ID = "1234567890123456789"
```

Save the file.

### Step 6 — Run it

In your terminal, navigate to the folder and run:

```bash
cd C:\Users\YourName\amazon-music-rpc
python amazon_music_rpc.py
```

You should see:

```
12:00:00  INFO     Amazon Music -> Discord RPC started (polling every 3s).
12:00:01  INFO     Connected to Discord RPC.
12:00:04  INFO     >  Blinding Lights - The Weeknd  [After Hours]
```

Keep the terminal open while you listen. Your Discord profile will update within a few seconds.

---

## What shows on your profile

| Field | What it displays |
|-------|-----------------|
| **Top line** | Song title (or artist name if title isn't available) |
| **Second line** | Artist and album |
| **Timer** | Counts down to end of song using the actual playback position |
| **Large icon** | Your uploaded logo (if configured) |
| **Small icon** | Playing or paused indicator |

The timer is sourced directly from Amazon Music's playback position, so it stays accurate even if you start the script mid-song or seek within a track.

> **Note:** Amazon Music inconsistently reports song titles and artists via the Windows media API — some tracks report both, some only report one. The script handles all cases gracefully.

---

## Autostart at login

To have the script run silently in the background every time you log in:

1. Press `Win + R`, type `shell:startup`, and hit Enter — this opens your Startup folder
2. Create a new file called `amazon_rpc.bat` in that folder with these contents:

```bat
@echo off
pythonw "C:\Users\YourName\amazon-music-rpc\amazon_music_rpc.py"
```

Replace the path with wherever you saved the script. Using `pythonw` instead of `python` suppresses the terminal window so it runs invisibly in the background.

---

## Troubleshooting

**`winsdk` install is stuck or taking forever**

This is normal — it's compiling C++ bindings. Wait at least 10 minutes before assuming something is wrong. If it does fail, try:
```bash
pip install winsdk --no-build-isolation
```

**"Discord not running" keeps looping**

Make sure the Discord **desktop app** is open. The browser version of Discord does not expose an RPC socket.

**Connected but nothing shows on my profile**

Go to Discord **User Settings → Activity Privacy** and make sure "Display current activity as a status message" is turned on.

**Script connects but no track is detected**

Check that Amazon Music is actually playing (not just open). Then verify it shows up in your Windows taskbar media widget — click the speaker icon in the bottom right. If it's not there, Windows can't see it either.

**Wrong app's music is showing**

If you run other media apps alongside Amazon Music (Spotify, VLC, etc.) and the wrong one shows, the script already filters specifically for Amazon Music's app ID. This should not happen under normal use.

**The progress bar is slightly off**

Amazon Music sometimes reports playback position with a small delay. The script re-syncs the position on every poll (every 3 seconds) so drift is minimal.

---

## Configuration reference

These values are at the top of `amazon_music_rpc.py` and can be changed:

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_CLIENT_ID` | `"YOUR_DISCORD_CLIENT_ID_HERE"` | Your Discord Application ID — **required** |
| `POLL_INTERVAL` | `3` | Seconds between track checks. Lower = more responsive, higher = less CPU |
| `LARGE_IMAGE_KEY` | `"amazon_music_logo"` | Key name of the image uploaded in Discord Developer Portal |
| `LARGE_IMAGE_TEXT` | `"Amazon Music"` | Tooltip text shown when hovering the large image |
| `FILTER_APP_NAME` | `"AmazonMobileLLC"` | Substring matched against the Windows media session app ID |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `winsdk` | Reads track info from the Windows SMTC API |
| `pypresence` | Sends data to Discord Rich Presence over local RPC |
| `psutil` | Process utilities (used during media session detection) |
