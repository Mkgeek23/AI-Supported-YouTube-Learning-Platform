## 📌 How to Install and Set up `ffmpeg`
FFmpeg is a versatile tool for handling multimedia data, offering capabilities for video and audio processing, conversions, streaming, and more.
### 🔧 Installation on Windows
If you have package managers installed, then `ffmpeg`
builds are available:
```bash
  choco install ffmpeg
```
```bash
  winget install "FFmpeg (Essentials Build)"
```
Otherwise follow the instructions below.

**Step 1: Download**
- Go to [FFmpeg Windows Builds](https://www.gyan.dev/ffmpeg/builds/) and download the latest "**ffmpeg-git-full**" build under the "**Release builds**" section
- Usually, this is provided as a `.zip` file

**Step 2: Extract Files**
- Extract the `.zip` archive into a convenient location, e.g., `C:\ffmpeg\`

**Step 3: Set Up Environment Variables**
To use FFmpeg from any Command Prompt window, add it to your Windows system environment path.
- Navigate to:
``` 
  Control Panel → System → Advanced system settings → Environment Variables
```
- Under "`System variables`", find and double-click "`Path`"
- Click "`New`" and add the path to your FFmpeg binaries (e.g., `C:\ffmpeg\bin`)
- Click "`OK`" to confirm changes

**Step 4: Verify Installation**
Open Command Prompt (`Win + R`, then type `cmd`), and run:
```bash
  ffmpeg -version
```
If FFmpeg was installed correctly, you should see its version number and configuration details.
### 🔧 Installation on Mac/Linux
**For Mac Users**
- The easiest way is to install via [Homebrew](https://brew.sh/):

1. Install Homebrew (If you haven't already):
``` bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
1. Install FFmpeg:
``` bash
  brew install ffmpeg
```
**For Linux (Ubuntu/Debian) Users**
- Using package manager (Recommended):

1. Update your repositories:
``` bash
  sudo apt update
```
2. Install FFmpeg:
``` bash
  sudo apt install ffmpeg
```

**Verify Installation (Mac/Linux):**

Verify successful installation by running the following in the Terminal:
``` bash
  ffmpeg -version
```
This will display the installed FFmpeg version, configuration, and other information.

🎉 **Done!** You've successfully installed and configured `ffmpeg` 🎉
