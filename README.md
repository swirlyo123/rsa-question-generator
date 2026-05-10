# RSA Question Generator

AI-powered question writer for RelationSh!t Advice (KSH).

## Running the app

### Windows
Double-click `start.ps1`, or run in terminal:
```
powershell -ExecutionPolicy Bypass -File start.ps1
```

### Mac
```
chmod +x start.sh
./start.sh
```

That's it. The script installs everything, sets up the API key, and gives you a public link automatically.

## Requirements
- Python 3.10+
- Internet connection (for Cloudflare tunnel)
- On Mac: [Homebrew](https://brew.sh) (the script uses it to install cloudflared)
