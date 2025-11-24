# Music Visualizer by Somyajeet

This is a simple audio visualizer made in Python. It plays .wav files and shows cool effects like neon bars and circles. It also has a particle system because particles look cool.

---

## Features

- **Neon Effects:** Bars glow.
- **Dual Modes:** Press `M` to switch between Bars and Circle.
- **Particles:** Dots float around when bass drops.
- **Playlist:** Click songs to play.
- **Seek Bar:** Drag the bottom bar to change time.
- **Downloader:** Script to download songs from YouTube easily.

---

## Setup

### If you use Linux

You need FFmpeg and PortAudio.

```bash
sudo apt update
sudo apt install ffmpeg portaudio19-dev python3-pyaudio
````

### If you use Windows

Just install FFmpeg and add it to path.

---

## How to Install

Clone this folder.

Make a virtual environment (optional but good):

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the libraries:

```bash
pip install -r requirements.txt
```

---

## How to Run

### Add Songs

Put `.wav` files in `songs` folder or use the downloader:

```bash
python downloader.py
```

### Start Player

```bash
python visualizer_player.py
```

---

## Controls

| Action                       | Key            |
| ---------------------------- | -------------- |
| Pause music                  | Spacebar       |
| Switch visualizer mode       | M              |
| Change bar size              | Up/Down Arrows |
| Fullscreen                   | F11            |
| Click songs or drag seek bar | Mouse          |

---

## License

Free to use.

```

Would you like a version with badges, screenshots section space, or installation video link section?
```
