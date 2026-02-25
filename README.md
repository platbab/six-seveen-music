
# Platbab Music Scraper

A multi-threaded GUI implementation for automated high-fidelity audio extraction. This tool functions as a high-performance wrapper for the `streamrip` engine, facilitating batch processing across multiple streaming platforms.

## Core Architecture

- **Parallelization**: Implements `ThreadPoolExecutor` for concurrent metadata resolution and audio retrieval tasks.
- **Cross-Platform Compatibility**: Supports native terminal spawning on Windows (CMD) and Linux (Konsole/X-Term/Gnome-Terminal).
- **Dynamic Configuration**: Direct TOML parsing and manipulation for real-time synchronization with local Streamrip settings.
- **Header Masquerading**: Custom headers to emulate standard browser behavior for metadata scraping from Spotify and Apple Music.

## Technical Requirements

- **Python 3.10+**
- **Streamrip** (initialized via `rip config --open`)
- **FFmpeg** (added to system PATH)

## Dependency Installation

```bash
pip install customtkinter ytmusicapi requests
