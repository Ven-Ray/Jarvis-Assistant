# Jarvis Voice Assistant

A sophisticated voice assistant inspired by J.A.R.V.I.S. from Iron Man, featuring a British butler personality, high-quality neural voices, real-time web search with AI-powered answers, and a futuristic PyQt6 frontend interface.

## Quick Start

Get Jarvis running in three steps:

### 1. Install Prerequisites
- **Python 3.8+** with pip package manager
- **LM Studio** - Download from https://lmstudio.ai/ and install on your machine

> **Note:** This project assumes you are already familiar with installing, configuring, and using LM Studio. Proper LM Studio configuration is essential for Jarvis to function correctly. Please consult the [official LM Studio documentation](https://lmstudio.ai/docs) for detailed instructions on setting up LM Studio, loading models, and running the local API server.

### 2. Install Dependencies
```bash
git clone <repository-url>
cd Jarvis-Project
pip install -r requirements.txt
```

### 3. Launch Jarvis
Start LM Studio with a model loaded, then run:
```bash
python run_frontend.py
```

On Windows, you can also launch Jarvis by running:
```bat
start_jarvis.bat
```

## System Requirements & Hardware Considerations

Jarvis runs entirely on your local hardware through LM Studio. Performance and response quality depend heavily on your system specifications and the AI model you choose to load.

### Model Size vs. Performance Tradeoffs
The size of the local LLM model you load directly affects both performance and answer quality:

| Model Size | RAM Required | Response Speed | Answer Quality | Best For |
|------------|--------------|----------------|----------------|----------|
| 1-3B parameters | 4-8 GB | Fastest | Basic | Simple commands, quick responses |
| 7-8B parameters | 8-16 GB | Moderate | Good | Balanced performance and quality |
| 13B+ parameters | 16-32+ GB | Slower | Excellent | Complex reasoning, detailed answers |

You can browse available models within LM Studio's built-in model library. Start small, test performance on your hardware, and scale up if you have the resources.

## Features

### Core Assistant
- **British Butler Personality**: Formal speech patterns with dry wit, addresses users as "Sir"
- **High-Quality Neural Voices**: Uses Microsoft's edge-tts with `en-GB-RyanNeural` (British male) for realistic speech
- **Voice-Activated Interface**: Speech recognition and text-to-speech capabilities
- **LM Studio AI Integration**: Connects to local LM Studio API for intelligent responses
- **LLM-Based Web Search Intent Classification**: Uses the LLM to determine if a query requires web search and generates optimized search queries automatically
- **Real-Time Web Search**: DuckDuckGo search integrated with AI synthesis for accurate, current answers
- **Smart Question Detection**: Questions are answered via web search + AI; commands use AI directly

### Futuristic Frontend
- **Animated Circular HUD**: Rotating rings with tick marks, pulsing core, state-based color changes
- **Audio Waveform Visualizer**: Real-time amplitude visualization with idle animation
- **Status Panel**: Current state display with activity history and timestamps
- **Chat Interface**: Primary text interaction with message history and scrollback
- **State Indicators**: Visual feedback for idle, listening, processing, speaking, and error states

### Voice Generation Engine
- **Reference Audio Processing**: Accepts MP3, WAV, M4A formats with validation and quality analysis
- **Consent-Based Storage**: Explicit consent tracking before saving reference voices
- **Voice Cloning**: Uses Coqui TTS XTTS v2 for high-quality voice synthesis from reference recordings
- **Duplicate Detection**: SHA-256 hashing to identify and reuse identical audio files

## Project Folder Structure

```
jarvis/
├── jarvis.py                    # Core voice assistant backend
├── run_frontend.py              # Frontend launcher script (recommended)
├── run_jarvis.py                # Easy launcher with prerequisite checks
├── start_jarvis.bat             # Windows batch file launcher
├── config.json                  # Configuration file for LM Studio, voice, search settings
├── requirements.txt             # Python dependencies
├── changelog.md                 # Version history and changes (local tracking)
├── README.md                    # This documentation file
│
├── frontend/                    # Futuristic PyQt6 UI package
│   ├── __init__.py
│   ├── main_window.py           # Main window with layout & backend integration
│   ├── hud_widget.py            # Animated circular HUD widget
│   ├── waveform_visualizer.py   # Real-time audio waveform display
│   └── status_panel.py          # State indicator + activity history
│
├── voice_gen/                   # Voice generation engine package
│   ├── __init__.py
│   ├── audio.py                 # Audio conversion & validation utilities
│   ├── storage.py               # Voice storage with consent tracking
│   ├── generation.py            # Coqui TTS XTTS v2 generation engine
│   └── cli.py                   # Command-line interface for voice gen operations
│
├── web_search/                  # Web search provider package
│   ├── __init__.py
│   ├── manager.py               # Search orchestration and provider management
│   ├── providers/               # Individual search provider implementations
│   │   ├── base.py              # Base provider interface
│   │   ├── weather.py           # Weather-specific search provider
│   │   ├── finance.py           # Financial data search provider
│   │   ├── sports.py            # Sports news and scores provider
│   │   ├── news.py              # General news search provider
│   │   ├── shopping.py          # Product and price comparison provider
│   │   ├── local.py             # Local business and service provider
│   │   └── general.py           # Fallback general web search provider
│   └── [other modules]          # Query building, ranking, validation utilities
│
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests for individual components
│   ├── integration/             # Integration tests for system workflows
│   └── web_search/              # Web search provider-specific tests
│
├── voice_records/               # Storage directory for reference voice recordings
├── reference_voices/            # Directory for reference audio files
└── output/                      # Generated output files (audio, logs)
```

## Configuration

### LM Studio API Setup
Jarvis connects to LM Studio's local API server. Ensure the following:

1. LM Studio is running with a model loaded
2. The API server is enabled and accessible at `http://localhost:1234/v1` (default)
3. Your firewall allows localhost connections on port 1234

For detailed instructions on configuring LM Studio's API, refer to the [LM Studio documentation](https://lmstudio.ai/docs).

### Jarvis Configuration File
Edit `config.json` to customize Jarvis settings:

```json
{
    "lm_studio": {
        "api_base": "http://localhost:1234/v1",
        "model": "default-model"
    },
    "voice": {
        "rate": 150,
        "volume": 1.0,
        "voice_id": "default"
    },
    "search": {
        "max_results": 5
    }
}
```

You can also change the API URL directly in the frontend's "Edit Local API" tab without editing the config file.

### Environment Variables (Optional)
Jarvis primarily uses `config.json` for configuration, but you may override settings with environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LM_STUDIO_API_BASE` | Override LM Studio API endpoint | `http://localhost:1234/v1` |
| `JARVIS_VOICE_RATE` | Speech rate in words per minute | `150` |
| `JARVIS_LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING) | `INFO` |

## Running the Project

### Option 1: Frontend GUI (Recommended)
```bash
python run_frontend.py
```
Launches the PyQt6 GUI with animated HUD, waveform visualizer, chat interface, and status panel. This is the primary way to interact with Jarvis through text chat or voice via the Listen button.

### Option 2: Easy Launcher (with prerequisite checks)
```bash
python run_jarvis.py
```
Checks for Python and LM Studio availability, then launches the frontend GUI. Provides helpful error messages if prerequisites are not met.

### Option 3: Windows Batch File (Windows only)
Double-click `start_jarvis.bat` to launch with automatic checks. This script verifies Python is available and attempts to connect to LM Studio before starting Jarvis.

### Verifying Functionality
After launching, verify that:
1. The frontend window appears with the animated HUD
2. The status panel shows "Idle" or similar ready state
3. You can type a message in the chat interface and receive a response
4. If using voice, click "LISTEN" and speak a test command

## Usage Examples

### Basic Voice Commands
```
User: "Hello"
Jarvis: "Good day, Sir. How may I assist you?"

User: "What's the weather today?"
Jarvis: [Searches web] "According to current forecasts, it will be partly cloudy with a high of 72°F."

User: "Search for latest AI news"
Jarvis: [Performs search and summarizes results]
```

### Text Chat Interaction
1. Type your message in the chat input field
2. Press Enter or click "Ask Jarvis"
3. Wait for response (processing indicator will show)
4. Use "Stop Chat" button to cancel an in-progress response

### Voice Generation CLI Examples
```bash
# Save a reference voice with consent
python voice_gen/cli.py save --name "Jarvis" --file "reference.mp3" --language en --consent

# List all saved voices
python voice_gen/cli.py list

# Generate speech using a saved voice
python voice_gen/cli.py generate --voice "Jarvis" --text "Hello, Sir." --output greeting.wav

# Delete a saved voice
python voice_gen/cli.py delete --voice "Jarvis"
```

## Troubleshooting

### Connection Issues
- Ensure LM Studio is running with a model loaded
- Verify API endpoint at `http://localhost:1234/v1` by visiting it in a browser or using curl
- Check the "Edit Local API" tab in the frontend to update the URL if needed

### Microphone Issues
- Check microphone permissions in system settings
- Test microphone separately using system tools (e.g., Windows Sound Settings)
- Ensure only one application is accessing the microphone at a time
- On Linux, verify ALSA/PulseAudio configuration

### Speech Synthesis Errors
If you see `Error during speech synthesis: [WinError 2] The system cannot find the file specified`:
- Install FFmpeg and add it to your PATH (recommended for fastest playback)
- Or ensure Windows Media Player COM objects are available
- Jarvis will automatically fall back to pyttsx3 if edge-tts fails

### Dependency Issues
- Run `pip install -r requirements.txt` to install all dependencies
- On Windows, PyAudio may require the Microsoft Visual C++ Build Tools
- If installation fails, try upgrading pip: `python -m pip install --upgrade pip`

### Frontend Display Issues
- The "Unknown property text-shadow" and similar warnings are harmless Qt stylesheet warnings
- They do not affect functionality or appearance
- Ensure your display supports the required resolution (minimum 1200x800 recommended)

### Web Search Not Working
- Ensure you have internet connectivity
- The assistant uses the `ddgs` package for DuckDuckGo search
- Check that no firewall is blocking outbound HTTP requests on port 443

## Development Guide

### Code Conventions
- Follow PEP 8 style guidelines for Python code
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep modules focused on single responsibilities

### Testing
Run the test suite to verify changes:
```bash
# Run all tests
python -m pytest tests/

# Run specific test category
python -m pytest tests/unit/
python -m pytest tests/integration/
```


## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

For issues, questions, or feature requests, please open an issue on the project's GitHub repository.
