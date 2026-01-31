# suno-download

Save complete metadata for ALL songs in your Suno.ai library (lyrics, prompts, style tags) and download MP3 files for public songs.

## Features

- Saves metadata for ALL songs in your library (public and private) to JSON
- Downloads MP3 files only for public songs
- Tracks library changes between runs
- Resumes downloads (skips already-downloaded files)
- No CAPTCHA service dependency (uses manual browser auth)

## Installation

### Option 1: Install from source (with virtual environment - recommended)

```bash
git clone https://github.com/andrewspringman/suno-download.git
cd suno-download

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Option 2: Install without virtual environment

```bash
git clone https://github.com/andrewspringman/suno-download.git
cd suno-download
pip install --user -e .
```

After installation, you can run the tool with either:
- `python3 -m suno_download` (works with both options)
- `suno-download` (command-line tool, requires virtual environment to be activated if using Option 1)

## Setup: Extract Authentication

Before using the tool, you need to extract authentication headers from your browser:

1. **Open Suno.ai in your browser**
   - Go to [suno.com](https://suno.com)
   - Log in to your account

2. **Open DevTools**
   - Press `F12` (or `Cmd+Option+I` on Mac)
   - Go to the **Network** tab

3. **Capture a request**
   - Navigate to your library to trigger API calls
   - Look for a request to `studio-api.prod.suno.com/api/feed/v3`
   - Click on the request to view details

4. **Copy required headers**
   - Find and copy these headers from the Request Headers:
     - `authorization` - starts with "Bearer ey..." (required)
     - `device-id` - a UUID like "abc-def-ghi-..." (required)
     - `cookie` - long string with cookies (optional - may not be needed)

5. **Save credentials**

   Create the file `~/.suno-download/auth.json`:

   ```bash
   mkdir -p ~/.suno-download
   nano ~/.suno-download/auth.json
   ```

   Add your credentials in this format:

   ```json
   {
     "authorization": "Bearer eyJ...",
     "device_id": "your-device-id-here"
   }
   ```

   Note: You can also add `"cookie": "..."` if you found it in the headers, but it may not be required for the v3 API.

### Alternative: Environment Variables

Instead of a config file, you can use environment variables:

```bash
export SUNO_AUTHORIZATION="Bearer eyJ..."
export SUNO_DEVICE_ID="your-device-id-here"
# export SUNO_COOKIE="__client=...; ..."  # Optional
```

## Usage

### Basic usage (with prompt for directory)

```bash
python -m suno_download
```

You'll be prompted for an output directory (default: `~/Music/suno-download`).

### Specify output directory

```bash
python -m suno_download ~/Music/my-suno-songs
```

### What gets downloaded

The tool will:

1. **Fetch** all songs from your Suno library via API (both public and private)
2. **Save** complete library snapshot to `suno_library.json` with metadata for ALL songs (lyrics, prompts, tags, etc.)
3. **Filter** to songs you've made public
4. **Download MP3 files** only for public songs as `{title}_{id}.mp3`
5. **Skip** already-downloaded MP3 files

### Output structure

```
~/Music/suno-download/
├── suno_library.json          # Complete metadata for all songs
├── My Song Title_abc123.mp3
├── Another Song_def456.mp3
└── ...
```

### Library snapshot (`suno_library.json`)

This file contains complete information about ALL songs in your library (not just public ones):

- Lyrics (`lyric`)
- Generation prompts (`prompt`, `gpt_description_prompt`)
- Style tags (`tags`, `negative_tags`)
- Metadata (title, created_at, duration, model_name, status)
- URLs (audio_url, video_url, image_url)

This enables future features like detecting library changes between runs.

## Troubleshooting

### "Authentication failed (401)"

Your credentials have expired. Re-extract headers from browser DevTools following the setup steps above.

### "No public songs to download"

The tool only downloads songs you've made public. To make songs public:

1. Go to [suno.com](https://suno.com)
2. Navigate to your library
3. Click the three-dot menu on each song
4. Select "Make Public"

### "Rate limited (429)"

If you hit Suno's rate limit:

- Wait 5-10 minutes before trying again
- The songs fetched before the rate limit will be saved in `suno_library.json`
- On retry, the tool will fetch all songs again (with delays to avoid rate limiting)

Note: The tool includes a 1.5s delay between pagination requests to minimize rate limiting, but you may still hit limits with large libraries.

### Downloads fail with network errors

- Check your internet connection
- Verify the song actually exists in your library
- Some songs may still be generating (check `status` in `suno_library.json`)

### macOS: Certificate errors

If you get SSL certificate errors:

```bash
pip install --upgrade certifi
```

## How It Works

1. **Authentication**: Uses headers extracted from your browser session (no automated login)
2. **API calls**: Fetches song data from `https://studio-api.prod.suno.com/api/feed/v3` using POST requests with cursor-based pagination
3. **Rate limiting**: Adds 1.5s delay between page requests to avoid hitting Suno's rate limits
4. **Downloads**: Fetches MP3 files from `https://cdn1.suno.ai/{song_id}.mp3`
5. **No CAPTCHA**: Since we use existing browser auth, no CAPTCHA solving is needed

## Privacy & Security

- Your credentials are stored locally in `~/.suno-download/auth.json` (never shared)
- The tool makes direct API calls to Suno (no third-party services)
- Downloaded files and metadata stay on your computer

## License

MIT License - see [LICENSE](LICENSE) file

## Disclaimer

This is an unofficial tool and is not affiliated with Suno.ai. Use responsibly and in accordance with Suno's terms of service.
