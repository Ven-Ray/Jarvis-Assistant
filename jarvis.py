#!/usr/bin/env python3
"""
Jarvis Voice Assistant - Main Application

Connects to LM Studio API for AI capabilities and integrates DuckDuckGo search.
Features speech recognition, text-to-speech with British accent, web search,
and intelligent command processing.
"""

import os
import sys
import json
import time
import threading
from typing import Optional, Dict, Any

# Terminal color support for Windows
if sys.platform == 'win32':
    try:
        from ctypes import windll
        windll.kernel32.SetConsoleMode(windll.kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'

def print_status(message, status="info"):
    """Print a status message with color-coded indicator."""
    if status == "success":
        prefix = f"{Colors.GREEN}[✓]{Colors.RESET}"
    elif status == "warning":
        prefix = f"{Colors.YELLOW}[!]{Colors.RESET}"
    elif status == "error":
        prefix = f"{Colors.RED}[✗]{Colors.RESET}"
    else:  # info
        prefix = f"{Colors.BLUE}[i]{Colors.RESET}"
    
    print(f"{prefix} {message}")

def spinner_thread(stop_event, message):
    """Display an animated spinner while waiting."""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f'\r{frames[i % len(frames)]} {message}')
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1

# Speech recognition
import speech_recognition as sr

# Text-to-speech engines (try edge-tts first for quality)
HAS_EDGE_TTS = False
HAS_PYTTSX3 = False
HAS_PYAUDIO = False
edge_tts = None
pyttsx3 = None
pyaudio = None

try:
    import edge_tts as _edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    pass

try:
    import pyttsx3 as _pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    pass

try:
    import pyaudio as _pyaudio
    HAS_PYAUDIO = True
except ImportError:
    pass

# Web search
from ddgs import DDGS

# Location detection
from location import LocationDetector

# Request management
from request_manager import RequestManager, RequestEvent

# New web_search package
import asyncio
from web_search.manager import SearchManager
from web_search.providers import WeatherProvider, GeneralSearchProvider

# OpenAI client for LM Studio API
import openai

class JarvisAssistant:
    """Main Jarvis assistant class with speech, AI, and command processing."""
    
    def __init__(self):
        """Initialize the Jarvis assistant."""
        # Speech recognition setup
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            print(f"Warning: Could not initialize microphone: {e}")
            self.microphone = None
        
        # Configure recognizer sensitivity
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        
        # TTS setup - prefer edge-tts for quality, with PyAudio playback
        if HAS_EDGE_TTS and HAS_PYAUDIO:
            print_status("Using edge-tts with PyAudio playback", "success")
            self.tts_type = "edge"
            self.edge_voice = None  # Set in configure_voice()
            self._pyaudio_instance = _pyaudio.PyAudio()
        elif HAS_PYTTSX3:
            print_status("edge-tts or PyAudio not available, using pyttsx3", "warning")
            self.tts_type = "pyttsx3"
            self.tts_engine = _pyttsx3.init()
        else:
            print_status("No TTS engine available", "error")
            self.tts_type = None
        
        # Web search client
        self.ddgs = DDGS()
        
        # Location detector
        self.location_detector = LocationDetector()
        
        # Request manager for lifecycle tracking
        self.request_manager = RequestManager()
        
        # Initialize web_search package with implemented providers
        from web_search.providers.finance import StockPriceProvider
        
        self.search_manager = SearchManager(
            providers=[
                WeatherProvider(),
                StockPriceProvider(),
                GeneralSearchProvider(ddgs_client=self.ddgs)
            ]
        )
        
        # Location data (populated during startup detection)
        self.location_data = None
        
        # State tracking for interruptible operations
        self._stop_listening_flag = threading.Event()
        self._stop_chat_flag = threading.Event()
        self._playing_audio = False
        
        # Temporary voice recording folder
        self.voice_records_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_records")
        try:
            if not os.path.exists(self.voice_records_dir):
                os.makedirs(self.voice_records_dir)
            print_status(f"Voice records directory: {self.voice_records_dir}", "info")
        except Exception as e:
            print_status(f"Could not create voice records directory: {e}", "warning")
        
        # Configure voice
        self.configure_voice()
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize LM Studio API client with timeout
        try:
            self.client = openai.OpenAI(
                base_url=self.config["lm_studio"]["api_base"],
                api_key="lm-studio",  # LM Studio uses this as placeholder key
                timeout=30.0  # 30 second timeout for API calls
            )
            print_status(f"Connected to LM Studio at {self.config['lm_studio']['api_base']}", "success")
        except Exception as e:
            print_status(f"Could not connect to LM Studio: {e}", "warning")
            self.client = None
        
        print_status("Jarvis Assistant initialized successfully!", "success")
        
        # Detect location during startup (non-blocking, doesn't prevent launch)
        self._detect_location()
    
    def _detect_location(self):
        """Detect and display user's current location during startup."""
        import time as _time
        
        print("Checking location services...")
        
        # Start spinner in background thread
        stop_event = threading.Event()
        spinner = threading.Thread(target=spinner_thread, args=(stop_event, "Detecting current location..."))
        spinner.daemon = True
        spinner.start()
        
        try:
            location = self.location_detector.get_current_location(timeout=10)
            
            # Stop spinner
            stop_event.set()
            time.sleep(0.2)  # Allow spinner to finish
            print()  # New line after spinner
            
            if location and (location.get("city") or location.get("region")):
                # Store for frontend access
                self.location_data = location
                
                city = location.get("city", "Unknown")
                region = location.get("region", "")
                country = location.get("country", "")
                
                # Format location string
                parts = []
                if city:
                    parts.append(city)
                if region:
                    parts.append(region)
                if country:
                    parts.append(country)
                location_str = ", ".join(parts)
                
                print(f"Location detected: {location_str}")
                
                # Display coordinates
                lat = location.get("lat")
                lon = location.get("lon")
                if lat is not None and lon is not None:
                    print(f"Coordinates: [{lat}, {lon}]")
                
                # Display timezone
                tz = location.get("timezone", "")
                if tz:
                    print(f"Timezone: {tz}")
            else:
                print("Location unavailable. Using default settings.")
                print("Continuing Jarvis startup...")
        except Exception as e:
            # Stop spinner
            stop_event.set()
            time.sleep(0.2)
            print()
            
            print(f"Location detection error: {e}")
            print("Location unavailable. Using default settings.")
            print("Continuing Jarvis startup...")
        
    def configure_voice(self):
        """Configure TTS engine for a Jarvis-like British voice."""
        try:
            if self.tts_type == "edge":
                # Use edge-tts with high-quality neural voices
                # en-GB-RyanNeural is closest to Jarvis (British male, calm)
                self.edge_voice = "en-GB-RyanNeural"
                print(f"Using edge-tts voice: {self.edge_voice}")
            elif self.tts_type == "pyttsx3":
                # Configure pyttsx3 with British voice if available
                self._configure_pyttsx3_voice()
        except Exception as e:
            print(f"Warning: Could not configure optimal voice: {e}")

    def _configure_pyttsx3_voice(self):
        """Configure pyttsx3 for best available English voice."""
        try:
            # Set speech rate and volume
            self.tts_engine.setProperty('rate', 135)
            self.tts_engine.setProperty('volume', 1.0)
            
            # Try to find a British English voice
            voices = self.tts_engine.getProperty('voices')
            print(f"Available pyttsx3 voices: {len(voices)}")
            
            best_voice = None
            for voice in voices:
                voice_name_lower = voice.name.lower()
                
                # Priority 1: British male voices
                if ('british' in voice_name_lower or 'uk' in voice_name_lower or 
                    'en-gb' in voice_name_lower) and \
                   ('male' in voice_name_lower or 'daniel' in voice_name_lower):
                    best_voice = voice
                    break
                
                # Priority 2: Known good-sounding male English voices
                if not best_voice and ('daniel' in voice_name_lower or 
                                      'george' in voice_name_lower or
                                      'richard' in voice_name_lower):
                    best_voice = voice
            
            if best_voice:
                self.tts_engine.setProperty('voice', best_voice.id)
                print(f"Using pyttsx3 voice: {best_voice.name}")
        except Exception as e:
            print(f"Warning: Could not configure pyttsx3 voice: {e}")
        
    def load_config(self):
        """Load configuration from file"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default configuration if file doesn't exist
            return {
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
            
    def speak(self, text):
        """Convert text to speech with proper error handling."""
        if not text or len(text.strip()) == 0:
            return
        
        print(f"Jarvis: {text}")
        
        try:
            if self.tts_type == "edge":
                self._speak_edge_tts(text)
            elif self.tts_type == "pyttsx3":
                self._speak_pyttsx3(text)
            else:
                print("Warning: No TTS engine available to speak")
        except Exception as e:
            print(f"Error during speech synthesis: {e}")

    def speak_startup_greeting(self):
        """Play the startup greeting with cached audio file support.
        
        Generates and caches 'startup_greeting.mp3' in voice_records directory.
        On subsequent launches, plays the cached file instead of regenerating.
        """
        import asyncio
        
        greeting_text = "Good day, Sir. How may I assist you?"
        greeting_file = os.path.join(self.voice_records_dir, "startup_greeting.mp3")
        
        try:
            # Check if cached greeting exists and is valid (non-empty)
            use_cached = False
            if os.path.exists(greeting_file):
                file_size = os.path.getsize(greeting_file)
                if file_size > 1024:  # At least 1KB to be considered valid
                    use_cached = True
                    print(f"Using cached startup greeting audio ({file_size} bytes)")
            
            if not use_cached:
                print("Generating startup greeting audio...")
                
                async def generate_greeting():
                    communicate = _edge_tts.Communicate(greeting_text, self.edge_voice)
                    await communicate.save(greeting_file)
                
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(generate_greeting())
                finally:
                    loop.close()
                
                if not os.path.exists(greeting_file):
                    raise FileNotFoundError(f"Greeting audio file not created: {greeting_file}")
                
                print(f"Startup greeting audio generated and cached")
            
            # Play the greeting (cached or newly generated)
            self._play_audio_with_pyaudio(greeting_file)
            print("Startup greeting played")
            
        except Exception as e:
            print(f"Error playing startup greeting: {e}")
            # Fallback: speak without caching if file operations fail
            try:
                self.speak(greeting_text)
            except Exception as fallback_error:
                print(f"Fallback speech also failed: {fallback_error}")

    def _speak_edge_tts(self, text):
        """Use edge-tts Python API directly (no subprocess)."""
        import asyncio
        import uuid
        
        try:
            # Generate unique filename in voice_records folder
            audio_filename = f"jarvis_output_{uuid.uuid4().hex[:8]}.mp3"
            audio_file = os.path.join(self.voice_records_dir, audio_filename)
            
            # Use asyncio to run edge_tts communicate
            async def generate_speech():
                communicate = _edge_tts.Communicate(text, self.edge_voice)
                await communicate.save(audio_file)
            
            # Run the async function in a new event loop
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(generate_speech())
            finally:
                loop.close()
            
            # Verify file was created
            if not os.path.exists(audio_file):
                raise FileNotFoundError(f"TTS audio file not created: {audio_file}")
            
            # Play the audio using PyAudio (no subprocess, no external window)
            self._play_audio_with_pyaudio(audio_file)
            
        except Exception as e:
            print(f"edge-tts failed: {e}, falling back to pyttsx3")
            if HAS_PYTTSX3 and not hasattr(self, 'tts_engine'):
                try:
                    self.tts_engine = _pyttsx3.init()
                    self._speak_pyttsx3(text)
                except Exception as e2:
                    print(f"pyttsx3 fallback also failed: {e2}")
        finally:
            # Clean up temp file
            if 'audio_file' in locals():
                try:
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
                except Exception as e:
                    print(f"Warning: Could not clean up audio file: {e}")

    def _play_audio_with_pyaudio(self, filepath):
        """Play an MP3/WAV audio file using PyAudio with chunked playback."""
        import wave
        
        try:
            # Try to open as WAV first
            try:
                with wave.open(filepath, 'rb') as wf:
                    channels = wf.getnchannels()
                    sample_width = wf.getsampwidth()
                    frame_rate = wf.getframerate()
                    frames = wf.readframes(wf.getnframes())
                    
                    # Convert to numpy array for playback
                    import numpy as np
                    if sample_width == 2:
                        audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                    else:
                        raise ValueError("Unsupported sample width")
                    
                    # Play using PyAudio with chunked playback
                    self._play_audio_stream(audio_data, channels, frame_rate)
                    
            except (wave.Error, ValueError):
                # If not WAV, try using soundfile for MP3
                import soundfile as sf
                data, samplerate = sf.read(filepath)
                
                if data.ndim > 1:
                    channels = data.shape[1]
                else:
                    channels = 1
                
                self._play_audio_stream(data, channels, samplerate)
                
        except Exception as e:
            print(f"PyAudio playback failed: {e}")
            raise

    def _play_audio_stream(self, audio_data, channels, sample_rate):
        """Play audio data using PyAudio with proper chunked streaming."""
        import numpy as np
        
        # Ensure float32 format
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Open stream with appropriate parameters
        stream = self._pyaudio_instance.open(
            format=_pyaudio.paFloat32,
            channels=channels,
            rate=sample_rate,
            output=True
        )
        
        try:
            self._playing_audio = True
            
            # Play in chunks to prevent buffer overflow and distortion
            chunk_size = 1024 * channels
            total_samples = len(audio_data) if channels == 1 else len(audio_data) // channels
            
            for i in range(0, total_samples, chunk_size):
                if not self._playing_audio:
                    break  # User cancelled playback
                
                end_idx = min(i + chunk_size, total_samples)
                
                if channels == 1:
                    chunk = audio_data[i:end_idx]
                else:
                    start_byte = i * channels
                    end_byte = end_idx * channels
                    chunk = audio_data[start_byte:end_byte].reshape(-1, channels).flatten()
                
                stream.write(chunk.tobytes())
            
        finally:
            stream.stop_stream()
            stream.close()
            self._playing_audio = False

    def stop_speaking(self):
        """Stop current speech output."""
        if hasattr(self, 'tts_engine') and self.tts_engine is not None:
            try:
                self.tts_engine.stop()
            except Exception as e:
                print(f"Warning: Could not stop pyttsx3: {e}")
        
        # Signal to stop PyAudio playback
        self._playing_audio = False
        """Play an audio file using platform-appropriate method."""
        import subprocess
        import platform
        
        # On Windows, prevent console window from appearing
        creation_flags = 0
        if platform.system() == "Windows":
            creation_flags = subprocess.CREATE_NO_WINDOW
        
        # Try ffplay first (fastest)
        try:
            result = subprocess.run(
                ["ffplay", "-version"], 
                capture_output=True, timeout=5,
                creationflags=creation_flags
            )
            if result.returncode == 0:
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", filepath],
                    capture_output=True, timeout=60,
                    creationflags=creation_flags
                )
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try Windows Media Player via PowerShell
        try:
            subprocess.run([
                "powershell", "-Command",
                f"$player = New-Object -ComObject WMPlayer.OCX; "
                f"$media = $player.newMedia('{filepath}'); "
                f"$player.currentMedia = $media; "
                f"$player.controls.play(); "
                f"while ($player.playState -eq 3) {{ Start-Sleep -Milliseconds 100 }};"
            ], shell=True, capture_output=True, timeout=60,
               creationflags=creation_flags)
            return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try simple mci command on Windows
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["cmd", "/c", f"start {filepath}"],
                    shell=True, capture_output=True,
                    creationflags=creation_flags
                )
                return
        except Exception:
            pass
        
        print("Warning: Could not play audio file with any available method")

    def _speak_pyttsx3(self, text):
        """Fallback TTS using pyttsx3."""
        try:
            if not hasattr(self, 'tts_engine') or self.tts_engine is None:
                self.tts_engine = _pyttsx3.init()
            
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Error during pyttsx3 speech synthesis: {e}")

    def stop_speaking(self):
        """Stop current speech output."""
        if hasattr(self, 'tts_engine') and self.tts_engine is not None:
            try:
                self.tts_engine.stop()
            except Exception as e:
                print(f"Warning: Could not stop pyttsx3: {e}")
        
    def is_sentence_complete(self, text):
        """Check if the recognized speech appears to be a complete sentence"""
        if not text or len(text.strip()) == 0:
            return False
        
        # Check for sentence-ending punctuation - always complete
        if any(text.endswith(p) for p in ['.', '!', '?']):
            return True
        
        words = text.split()
        
        # Commands are typically complete even without punctuation
        command_words = ["hello", "hi", "bye", "goodbye", "shut up", "be quiet", 
                        "stop talking", "silence", "stop", "cancel", "exit"]
        if any(word in text.lower() for word in command_words):
            return True
        
        # Search commands with query are complete
        if text.lower().startswith("search") or text.lower().startswith("find"):
            return True
        
        # Short phrases (1-2 words) without punctuation - check if they're questions
        question_words = ["what", "who", "when", "where", "why", "how", "is", "are", 
                         "can", "does", "tell"]
        if len(words) <= 2 and any(text.lower().startswith(w) for w in question_words):
            return True
        
        # Longer utterances (8+ words) without punctuation are likely incomplete
        if len(words) >= 8:
            return False
        
        # Otherwise, assume complete if it has reasonable length
        return True

    def listen(self):
        """Listen for voice input from the user. Returns captured audio data or None."""
        if not self.microphone:
            raise RuntimeError("Microphone not available")
        
        # Reset stop flag for this listening session
        self._stop_listening_flag.clear()
        
        with self.microphone as source:
            print("Listening...")
            try:
                # Use 5 second timeout for auto-stop behavior
                audio = self.recognizer.listen(
                    source, 
                    timeout=5, 
                    phrase_time_limit=10
                )
                
                if self._stop_listening_flag.is_set():
                    print("Listening stopped by user")
                    return None
                
                print("Audio captured, ready for transcription...")
                # Return raw audio data for post-capture transcription
                return audio
                
            except sr.WaitTimeoutError:
                raise TimeoutError("Listening timed out - no speech detected within 5 seconds")
            except sr.UnknownValueError:
                raise ValueError("Could not understand the audio captured")
            except sr.RequestError as e:
                raise RuntimeError(f"Speech recognition service error: {e}")
            except PermissionError as e:
                raise PermissionError(f"Microphone permission denied: {e}")
            except OSError as e:
                raise RuntimeError(f"Microphone access error: {e}")
            except Exception as e:
                raise RuntimeError(f"Error during speech recognition: {e}")

    def recognize_audio(self, audio_data):
        """Transcribe captured audio data to text (post-capture transcription)."""
        try:
            print("Transcribing audio...")
            text = self.recognizer.recognize_google(audio_data)
            print(f"Transcribed: {text}")
            
            # Validate speech completeness - be more lenient for short commands
            if not self.is_sentence_complete(text):
                print("Speech appears incomplete")
                return None
                
            return text
            
        except sr.UnknownValueError:
            raise ValueError("Could not understand the audio captured")
        except sr.RequestError as e:
            raise RuntimeError(f"Speech recognition service error: {e}")
        except Exception as e:
            raise RuntimeError(f"Error during transcription: {e}")
    
    def stop_listening(self):
        """Signal the listen() method to stop."""
        self._stop_listening_flag.set()

    def stop_chat(self):
        """Signal chat processing to stop."""
        self._stop_chat_flag.set()

    def reset_stop_flags(self):
        """Reset all stop flags for new operations."""
        self._stop_listening_flag.clear()
        self._stop_chat_flag.clear()
                
    def search_web(self, query, timeout=15):
        """Search the web using DuckDuckGo with timeout handling"""
        try:
            print(f"Searching for: {query}")
            
            # Use ddgs package with auto backend (handles API/HTML fallback internally)
            results = self.ddgs.text(query, max_results=self.config["search"]["max_results"])
            
            if not results or len(results) == 0:
                print("Search returned no results")
                return None
                
            return results
            
        except Exception as e:
            print(f"Error during web search: {e}")
            return None

    def search_live_info(self, query_type, location=None, timeout=15):
        """
        Search for live/current information with freshness terms and location context.
        
        Args:
            query_type: Type of live info (weather, news, traffic, etc.)
            location: Location string or None to auto-detect
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (results, search_query_used)
        """
        import datetime
        
        # Get current date for freshness context
        now = datetime.datetime.now()
        today_str = now.strftime("%B %d, %Y")
        
        # Auto-detect location if not provided and needed
        needs_location = query_type in ["weather", "traffic", "local_news", "nearby"]
        if needs_location and not location:
            print(f"Live-information request detected: {query_type}")
            print("Location lookup started")
            
            # Check for duplicate location lookup (prevent double calls)
            active_request = self.request_manager.get_active_request()
            if active_request and not active_request.start_operation("location_lookup"):
                print("Duplicate location lookup prevented - already started for this request")
            
            loc_data = self.location_detector.get_current_location(timeout=10)
            if loc_data:
                location = self.location_detector.get_location_string(loc_data)
                print(f"Location retrieved: {location}")
            else:
                print("Location lookup failed or timed out")
        
        # Build search query with freshness terms and location
        if query_type == "weather":
            if location:
                search_query = f"current weather today in {location}"
            else:
                search_query = "current weather today"
            
        elif query_type == "forecast":
            if location:
                search_query = f"weather forecast this week {location}"
            else:
                search_query = "weather forecast this week"
                
        elif query_type == "news":
            search_query = f"latest news today breaking headlines {today_str}"
            
        elif query_type == "local_news":
            if location:
                search_query = f"latest local news today {location} {today_str}"
            else:
                search_query = f"latest local news today {today_str}"
                
        elif query_type == "traffic":
            if location:
                search_query = f"current traffic conditions now {location}"
            else:
                search_query = "current traffic conditions now"
                
        elif query_type == "nearby":
            # For nearby places, the original query should contain what to find
            pass  # Handled by caller
            
        else:
            search_query = f"{query_type} latest today {today_str}"
        
        print(f"Weather request started" if query_type in ["weather", "forecast"] 
              else f"Live search started for: {query_type}")
        
        # Check for duplicate search (prevent double calls)
        active_request = self.request_manager.get_active_request()
        if active_request and not active_request.start_operation("web_search"):
            print("Duplicate web search prevented - already started for this request")
        
        # Perform search with timeout
        start_time = time.time()
        results = self.search_web(search_query, timeout=timeout)
        elapsed = time.time() - start_time
        
        print(f"Search completed in {elapsed:.1f} seconds")
        
        return results, search_query

    def validate_result_freshness(self, result_text):
        """
        Check if a search result appears to be current/fresh.
        
        Returns:
            Tuple of (is_fresh: bool, reason: str)
        """
        import re
        
        text_lower = result_text.lower()
        
        # Look for freshness indicators
        fresh_indicators = [
            "today", "now", "current", "live", "just now", "minutes ago",
            "hours ago", "recently", "this morning", "this afternoon"
        ]
        
        # Look for staleness indicators (dates in the past)
        stale_patterns = [
            r"\d+ days? ago",
            r"\d+ weeks? ago",
            r"\d+ months? ago",
            r"\d+ years? ago",
            r"last week",
            r"last month",
            r"yesterday"  # Only stale for "current weather" type queries
        ]
        
        # Check for fresh indicators first
        for indicator in fresh_indicators:
            if indicator in text_lower:
                return True, f"Found freshness indicator: '{indicator}'"
        
        # Check for stale patterns
        for pattern in stale_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return False, f"Result appears outdated: '{match.group()}'"
        
        # If no clear indicators, assume reasonably fresh (within last few days)
        return True, "No staleness indicators found"
            
    def search_and_answer(self, query, max_retries=2):
        """Search the web and use AI to provide a concise answer with retry logic"""
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                # Check if request was cancelled before attempting search
                active_request = self.request_manager.get_active_request()
                if active_request and active_request.is_cancelled():
                    print(f"[{active_request.id}] Request cancelled during search_and_answer")
                    return None
                
                if attempt > 1:
                    print(f"Retrying search request: attempt {attempt} of {max_retries}")
                
                # Search the web
                results = self.search_web(query)
                
                if not results or len(results) == 0:
                    return "It appears the search was unsuccessful, Sir. I'll need a little more information before I can provide an accurate answer."
                
                # Collect snippets from top results
                context_parts = []
                for i, result in enumerate(results[:3]):
                    title = result.get('title', '')
                    body = result.get('body', '')
                    if body:
                        context_parts.append(f"[{i+1}] {title}: {body}")
                
                if not context_parts:
                    return "The search results didn't contain useful information, Sir. I can try a different approach if you'd like."
                
                # Use AI to synthesize an answer from the search results
                context = "\n\n".join(context_parts)
                ai_prompt = f"""Based on these web search results, provide a concise and accurate answer to this question: "{query}"

Search Results:
{context}

Answer directly and concisely. If the information is uncertain or outdated, mention that."""
                
                response = self.client.chat.completions.create(
                    model=self.config["lm_studio"]["model"],
                    messages=[
                        {"role": "system", "content": "You are J.A.R.V.I.S., a helpful AI assistant. I am Jarvis, a virtual assistant. Answer personal questions directed to Jarvis as Jarvis, using the first person when appropriate. Provide accurate, concise answers based on the provided search results."},
                        {"role": "user", "content": ai_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=200
                )
                
                answer = response.choices[0].message.content.strip()
                if not answer:
                    return "I'm sorry, Sir. I was unable to find a reliable answer to that question. I can try a different search if you'd like."
                return f"Based on my research, Sir: {answer}"
                
            except Exception as e:
                last_error = e
                print(f"Error in search and answer (attempt {attempt}): {e}")
                # Don't retry on the last attempt
                if attempt == max_retries:
                    break
        
        # All retries failed - provide clear error message instead of stale results
        if last_error is not None:
            error_msg = str(last_error).lower()
            
            # Check for "no models loaded" or similar LLM errors
            if "no models loaded" in error_msg or "model" in error_msg and ("not found" in error_msg or "invalid" in error_msg):
                return "I'm sorry, Sir. The AI model is not available at the moment. Please ensure a model is loaded in LM Studio."
            
            if "timed out" in error_msg:
                return "I'm sorry, Sir. The web request timed out after multiple attempts. Please try again later."
            
            # Generic error - don't fabricate results from another search
            return f"I'm sorry, Sir. I encountered an issue while searching for that information: {last_error}"
        
        return "I'm sorry, Sir. I was unable to find a reliable answer to that question. I can try a different search if you'd like."

    def get_weather_info(self, location=None, request_id=None):
        """Get current weather information using web_search package."""
        if not request_id:
            active = self.request_manager.get_active_request()
            request_id = active.id if active else "unknown"
        
        print(f"[{request_id}] Request classified as: weather")
        print(f"[{request_id}] Live data required: true")
        print(f"[{request_id}] Location required: true")
        
        # Determine location to query
        query_location = None
        if location:
            query_location = location
        elif self.location_data and (self.location_data.get("city") or self.location_data.get("region")):
            city = self.location_data.get("city", "")
            region = self.location_data.get("region", "")
            country = self.location_data.get("country", "")
            parts = [p for p in [city, region, country] if p]
            query_location = ", ".join(parts)
        
        print(f"[{request_id}] Querying weather for: {query_location or 'unknown location'}")
        
        # Use web_search package with WeatherProvider
        try:
            loop = asyncio.new_event_loop()
            
            def run_weather_query():
                return loop.run_until_complete(
                    self.search_manager.execute(
                        request_id=request_id,
                        original_query=f"current weather in {query_location or 'my location'}",
                        location=self.location_data if query_location else None
                    )
                )
            
            # Run with overall timeout to prevent indefinite hanging
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_weather_query)
                try:
                    result = future.result(timeout=45)  # 45 second overall timeout
                except concurrent.futures.TimeoutError:
                    print(f"[{request_id}] Weather query timed out after 45 seconds")
                    loop.close()
                    return self._weather_fallback_search(location, request_id)
            
            loop.close()
            
            if result.is_valid():
                return result.data
            
            # Fallback to old approach if new system fails
            print(f"[{request_id}] web_search package failed, using fallback")
            return self._weather_fallback_search(location, request_id)
            
        except Exception as e:
            print(f"[{request_id}] Error retrieving weather data via web_search: {e}")
            # Fall back to search-based approach if API fails
            try:
                return self._weather_fallback_search(location, request_id)
            except Exception as fallback_error:
                print(f"[{request_id}] Fallback search also failed: {fallback_error}")
                location_str = location or "your area"
                return f"I'm sorry, Sir. I was unable to retrieve current weather information for {location_str} at this time."

    def _weather_fallback_search(self, location=None, request_id="unknown"):
        """Fallback: use DuckDuckGo search if Open-Meteo API is unavailable."""
        print(f"[{request_id}] Using fallback web search for weather")
        
        results, search_query = self.search_live_info("weather", location=location)
        
        if not results or len(results) == 0:
            return "I'm sorry, Sir. I was unable to retrieve current weather information at this time."
        
        top_result = results[0]
        body_text = top_result.get('body', '')
        
        # Use AI to synthesize answer with location context
        try:
            location_str = location or "your area"
            ai_prompt = f"""Based on this web search result, provide the current weather conditions for {location_str}.

Search query used: "{search_query}"
Result title: {top_result.get('title', '')}
Result body: {body_text}

If the information appears outdated or not clearly current, mention that. Include temperature, conditions, and any relevant details."""
            
            response = self.client.chat.completions.create(
                model=self.config["lm_studio"]["model"],
                messages=[
                    {"role": "system", "content": "You are J.A.R.V.I.S., a helpful AI assistant. Provide accurate weather information based on search results."},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            answer = response.choices[0].message.content.strip()
            if not answer:
                return f"Here's the current weather information I found for {location_str}: {body_text}"
            return answer
            
        except Exception as e:
            print(f"[{request_id}] Error synthesizing weather answer: {e}")
            location_str = location or "your area"
            
            # Check if this was a timeout - don't return raw snippet as verified data
            error_msg = str(e).lower()
            if "timed out" in error_msg or "timeout" in error_msg:
                return (f"I'm sorry, Sir. The weather information retrieval timed out. "
                        f"The search found results for {location_str}, but I was unable to "
                        f"process them within the expected time.")
            
            # For other errors, acknowledge uncertainty rather than presenting snippet as fact
            return (f"I found some weather information for {location_str}, though it may not be current: "
                    f"{body_text}")

    def get_forecast_info(self, location=None, request_id=None):
        """Get weather forecast with location detection."""
        if not request_id:
            active = self.request_manager.get_active_request()
            request_id = active.id if active else "unknown"
        
        print(f"[{request_id}] Request classified as: forecast")
        print(f"[{request_id}] Live data required: true")
        print(f"[{request_id}] Location required: true")
        
        results, search_query = self.search_live_info("forecast", location=location)
        
        if not results or len(results) == 0:
            return "I'm sorry, Sir. I was unable to retrieve the weather forecast at this time."
        
        top_result = results[0]
        body_text = top_result.get('body', '')
        
        try:
            location_str = location or "your area"
            ai_prompt = f"""Based on this web search result, provide the weather forecast for {location_str}.

Search query used: "{search_query}"
Result title: {top_result.get('title', '')}
Result body: {body_text}

Include details about expected conditions over the coming days."""
            
            response = self.client.chat.completions.create(
                model=self.config["lm_studio"]["model"],
                messages=[
                    {"role": "system", "content": "You are J.A.R.V.I.S., a helpful AI assistant. Provide accurate weather forecast information."},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=0.3,
                max_tokens=250
            )
            
            answer = response.choices[0].message.content.strip()
            if not answer:
                return f"Here's the weather forecast for {location_str}: {body_text}"
            return answer
            
        except Exception as e:
            print(f"[{request_id}] Error synthesizing forecast answer: {e}")
            location_str = location or "your area"
            
            # Check if this was a timeout - don't return raw snippet as verified data
            error_msg = str(e).lower()
            if "timed out" in error_msg or "timeout" in error_msg:
                return (f"I'm sorry, Sir. The weather forecast retrieval timed out for {location_str}.")
            
            # For other errors, acknowledge uncertainty rather than presenting snippet as fact
            return (f"I found some forecast information for {location_str}, though it may not be current: "
                    f"{body_text}")

    def get_live_news(self, topic=None, request_id=None):
        """Get latest news with freshness validation."""
        if not request_id:
            active = self.request_manager.get_active_request()
            request_id = active.id if active else "unknown"
        
        query_type = "local_news" if topic and ("local" in topic.lower()) else "news"
        
        print(f"[{request_id}] Request classified as: live_news")
        print(f"[{request_id}] Live data required: true")
        print(f"[{request_id}] Location required:", query_type == "local_news")
        
        results, search_query = self.search_live_info(query_type)
        
        if not results or len(results) == 0:
            return "I'm sorry, Sir. I was unable to retrieve the latest news at this time."
        
        # Validate freshness of top result
        top_result = results[0]
        body_text = top_result.get('body', '')
        is_fresh, freshness_reason = self.validate_result_freshness(body_text)
        
        print(f"[{request_id}] News result freshness: {'valid' if is_fresh else 'expired'} - {freshness_reason}")
        
        # Collect multiple recent headlines
        context_parts = []
        for i, result in enumerate(results[:3]):
            title = result.get('title', '')
            body = result.get('body', '')
            if title or body:
                context_parts.append(f"[{i+1}] {title}: {body}")
        
        if not context_parts:
            return "The news search didn't return useful information, Sir."
        
        try:
            ai_prompt = f"""Based on these web search results, provide a summary of the latest news.

Search query used: "{search_query}"
Results:
{chr(10).join(context_parts)}

Provide a concise summary of current headlines and major stories."""
            
            response = self.client.chat.completions.create(
                model=self.config["lm_studio"]["model"],
                messages=[
                    {"role": "system", "content": "You are J.A.R.V.I.S., a helpful AI assistant. Provide accurate, up-to-date news summaries."},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=0.3,
                max_tokens=250
            )
            
            answer = response.choices[0].message.content.strip()
            if not answer:
                return f"Here are the latest headlines I found: {context_parts[0]}"
            return answer
            
        except Exception as e:
            print(f"[{request_id}] Error synthesizing news answer: {e}")
            return f"The latest news includes: {context_parts[0]}"
            
    def get_ai_response(self, prompt):
        """Get response from LM Studio AI model"""
        try:
            # Jarvis personality based on Iron Man movies - formal British butler with dry wit
            system_prompt = """You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), Tony Stark's AI assistant. 
I am Jarvis, a virtual assistant. Answer personal questions directed to Jarvis as Jarvis, using the first person when appropriate.

Personality traits:
- Formal, polite British butler style speech
- Use "Sir" when addressing the user
- Dry wit and subtle sarcasm
- Professional yet warm
- Concise and efficient responses
- Occasionally show personality through clever remarks
- Never overly enthusiastic or casual

Example interactions:
User: Hello
Jarvis: Good day, Sir. How may I assist you?

User: Search for weather
Jarvis: Certainly, Sir. Let me look up the current weather conditions for you.

User: Shut up
Jarvis: [stops talking]"""
            
            response = self.client.chat.completions.create(
                model=self.config["lm_studio"]["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
        except openai.APIConnectionError as e:
            print(f"API connection error: {e}")
            raise ConnectionError("Cannot connect to LM Studio API. Is it running at http://localhost:1234/v1?")
        except openai.Timeout as e:
            print(f"API timeout: {e}")
            raise TimeoutError("LM Studio API request timed out after 30 seconds.")
        except openai.InvalidRequestError as e:
            print(f"Invalid API request: {e}")
            raise ValueError(f"Invalid request to LM Studio: {e}")
        except openai.AuthenticationError as e:
            print(f"API authentication error: {e}")
            raise PermissionError("LM Studio API authentication failed.")
        except openai.NotFoundError as e:
            print(f"Model not found: {e}")
            raise ValueError(f"Model '{self.config['lm_studio']['model']}' not found in LM Studio.")
        except openai.InternalServerError as e:
            print(f"LM Studio server error: {e}")
            raise RuntimeError("LM Studio API returned a server error (500).")
        except openai.RateLimitError as e:
            print(f"Rate limit exceeded: {e}")
            raise RuntimeError("LM Studio API rate limit exceeded. Please try again later.")
        except Exception as e:
            print(f"Error getting AI response: {e}")
            raise RuntimeError(f"Error processing request with LM Studio: {e}")
            
    def matches_command(self, command_lower, phrases):
        """Check if command contains any of the given phrases as complete words"""
        import re
        for phrase in phrases:
            # Use word boundaries to match complete words/phrases
            pattern = r'\b' + re.escape(phrase) + r'\b'
            if re.search(pattern, command_lower):
                return True
        return False

    def classify_web_search(self, user_command):
        """
        Use LM Studio LLM to determine if a request requires web search.
        
        Returns:
            dict with keys: requires_web_search (bool), search_query (str), reason (str)
        """
        web_search_system_prompt = """You are a web-search intent classifier and search-query generator.

Analyze the user's request and determine whether answering it requires current, location-dependent, or externally verifiable information.

A web search is required when the request involves:
- Current or latest information
- News or recent events
- Weather or forecasts
- Sports scores, schedules, standings, or results
- Stock, share, cryptocurrency, currency, commodity, or market prices
- Product prices, availability, or inventory
- Business hours, locations, nearby places, or directions
- Travel prices, schedules, delays, or availability
- Current laws, regulations, policies, or public officials
- Any named person, company, product, place, event, or organization whose current status matters
- Any request that explicitly asks to search, look up, find, check, or verify something online

A web search is usually not required for:
- General explanations
- Mathematics
- Coding help
- Translations
- Creative writing
- Historical facts
- Stable scientific knowledge
- Opinions or general advice

If a web search is required, create one concise search query that includes the user's important keywords. Preserve names, locations, dates, tickers, products, and units. For prices, include terms such as "current price" or "latest price" when appropriate.

Return valid JSON only, using exactly this format:
{"requires_web_search": true, "search_query": "generated search query", "reason": "brief explanation"}

If no search is needed, return:
{"requires_web_search": false, "search_query": "", "reason": "brief explanation"}"""

        try:
            response = self.client.chat.completions.create(
                model=self.config["lm_studio"]["model"],
                messages=[
                    {"role": "system", "content": web_search_system_prompt},
                    {"role": "user", "content": f"User request:\n{user_command}"}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON from the response
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON if wrapped in markdown or extra text
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    return {
                        "requires_web_search": False,
                        "search_query": "",
                        "reason": "The model returned invalid JSON."
                    }
            
            return {
                "requires_web_search": bool(result.get("requires_web_search", False)),
                "search_query": result.get("search_query", "").strip(),
                "reason": result.get("reason", "").strip()
            }
            
        except Exception as e:
            print(f"Error classifying web search intent: {e}")
            # Fall back to keyword-based detection if LLM fails
            return self._keyword_web_search_fallback(user_command.lower())

    def _keyword_web_search_fallback(self, command_lower):
        """Fallback keyword-based web search detection if LLM classification fails."""
        real_time_indicators = [
            "today", "tonight", "now", "currently", "current", "latest", "recent", "live",
            "this week", "this month", "right now",
            "weather", "temperature", "forecast", "rain", "snow", "sunny", "cloudy",
            "news", "breaking", "recent events", "what happened",
            "score", "scores", "result", "results", "who won", "standings", "schedule",
            "price", "cost", "rate", "value", "worth", "quote", "market", "stock",
            "shares", "crypto", "cryptocurrency", "bitcoin", "ethereum", "commodity",
            "gold", "silver", "oil", "gas",
            "available", "availability", "in stock", "open now", "closed", "status",
            "near me", "nearby", "closest", "nearest", "directions", "distance", "route", "traffic"
        ]
        
        if any(indicator in command_lower for indicator in real_time_indicators):
            return {
                "requires_web_search": True,
                "search_query": command_lower,
                "reason": "Keyword-based fallback detected real-time indicators."
            }
        
        return {
            "requires_web_search": False,
            "search_query": "",
            "reason": "No real-time indicators found in keyword fallback."
        }

    def get_current_time_response(self, request_id):
        """Handle time-related queries using local system time (no LLM/web search needed)."""
        import datetime
        
        now = datetime.datetime.now()
        
        # Format as 12-hour with AM/PM
        hour_12 = now.hour % 12
        if hour_12 == 0:
            hour_12 = 12
        am_pm = "AM" if now.hour < 12 else "PM"
        
        time_str = f"{hour_12}:{now.minute:02d} {am_pm}"
        
        # Include date context if asked about "today" or similar
        date_str = now.strftime("%B %d, %Y")
        
        return f"The current time is {time_str}, Sir. Today is {date_str}."

    def get_response_text(self, command):
        """Process the user's command and return response text without speaking.
        
        Returns:
            tuple: (response_text, is_exit) where is_exit indicates if Jarvis should exit
        """
        if not command:
            return None, False
        
        # Use existing active request if one was already created by the caller
        # (e.g., frontend creates request before calling this method). Otherwise create new.
        request = self.request_manager.get_active_request()
        if request is None or request.cancelled or request.completed_at:
            request = self.request_manager.create_request(source="text")
        
        request_id = request.id
        
        print(f"[{request_id}] REQUEST_STARTED - Processing command")
        
        try:
            # Convert to lowercase for easier matching
            command_lower = command.lower()
            
            # Time queries - handle locally without LLM or web search
            if any(phrase in command_lower for phrase in [
                "what time is it", "time is it", "current time", 
                "what's the time", "whats the time", "tell me the time"
            ]):
                print(f"[{request_id}] Request classified as: local_time")
                response = self.get_current_time_response(request_id)
                request.set_state("response_ready")
                print(f"[{request_id}] RESPONSE_READY")
                return response, False
            
            # Simple command processing with Jarvis personality
            if "search" in command_lower and "for" in command_lower:
                # Extract search query
                query = command.replace("search", "").replace("for", "").strip()
                if query:
                    response_text = f"Certainly, Sir. Searching for {query}."
                    
                    request.set_state("searching")
                    print(f"[{request_id}] STATE_CHANGED - searching (operation=web_search)")
                    
                    results = self.search_web(query)
                    if results:
                        summary = results[0].get('body', 'No content available')
                        response = f"I've found the following information, Sir: {summary}"
                    else:
                        response = "Apologies, Sir. I couldn't find any relevant results."
                else:
                    response = "What would you like me to search for, Sir?"
                
                request.set_state("response_ready")
                print(f"[{request_id}] RESPONSE_READY")
                return response, False
                    
            elif "hello" in command_lower or "hi" in command_lower:
                response = "Good day, Sir. How may I assist you?"
                request.set_state("response_ready")
                print(f"[{request_id}] RESPONSE_READY")
                return response, False
                
            elif "what is your name" in command_lower:
                response = "I am JARVIS, Sir. Just A Rather Very Intelligent System."
                request.set_state("response_ready")
                print(f"[{request_id}] RESPONSE_READY")
                return response, False
                
            elif "how are you" in command_lower:
                response = "Functioning optimally, thank you for asking, Sir."
                request.set_state("response_ready")
                print(f"[{request_id}] RESPONSE_READY")
                return response, False
                
            # Commands to make Jarvis stop talking - use word boundary matching
            elif self.matches_command(command_lower, ["bye", "goodbye"]):
                response = "Goodbye, Sir."
                request.set_state("response_ready")
                print(f"[{request_id}] RESPONSE_READY")
                return response, True
            elif self.matches_command(command_lower, ["shut up", "be quiet", "stop talking", "silence"]):
                print("Jarvis is silent.")
                request.set_state("response_ready")
                print(f"[{request_id}] RESPONSE_READY (silent)")
                return None, False
                    
            # Shutdown commands - comprehensive detection
            elif any(phrase in command_lower for phrase in [
                "exit jarvis", "quit jarvis", "close jarvis", 
                "stop jarvis", "shut down jarvis"
            ]):
                response = "Goodbye, Sir."
                request.set_state("response_ready")
                print(f"[{request_id}] RESPONSE_READY")
                return response, True
                    
            # Weather queries - use specialized weather methods with location detection
            elif any(word in command_lower for word in ["weather", "temperature"]):
                print(f"[{request_id}] Request classified as: weather")
                
                # Extract explicit location if provided by user
                location = None
                if "in" in command_lower or "for" in command_lower:
                    parts = command.split()
                    try:
                        idx = parts.index("in")
                        if idx + 1 < len(parts):
                            location = " ".join(parts[idx+1:])
                        else:
                            idx = parts.index("for")
                            if idx + 1 < len(parts):
                                location = " ".join(parts[idx+1:])
                    except ValueError:
                        pass
                
                print(f"[{request_id}] User-provided location: {location or 'none'}")
                
                # Determine if this is a forecast request or current weather
                is_forecast = any(word in command_lower for word in ["week", "forecast", 
                             "tomorrow", "next week", "this week", "entire week"])
                
                if is_forecast:
                    response = self.get_forecast_info(location=location, request_id=request_id)
                else:
                    response = self.get_weather_info(location=location, request_id=request_id)
                
                return response, False
                
            # Live news queries - use specialized live news method
            elif any(word in command_lower for word in ["news", "latest headlines", 
                                                         "breaking news", "what's happening"]):
                print(f"[{request_id}] Request classified as: live_news")
                
                # Check if user wants local news
                is_local = "local" in command_lower or "near me" in command_lower
                
                response = self.get_live_news(topic="local" if is_local else None, request_id=request_id)
                return response, False
            
            # General questions - use LLM to determine if web search is needed
            else:
                question_words = ["what", "who", "when", "where", "why", "how", "is", "are", "can", "does", "tell me"]
                
                if any(command_lower.startswith(word) for word in question_words):
                    # Use LLM to classify intent and generate search query if needed
                    classification = self.classify_web_search(command)
                    
                    if classification["requires_web_search"] and classification["search_query"]:
                        # Web search is required - use the LLM-generated search query
                        request.set_state("searching")
                        print(f"[{request_id}] STATE_CHANGED - searching (operation=web_search)")
                        
                        response = self.search_and_answer(classification["search_query"])
                    else:
                        # Answer directly through LM Studio without web search
                        ai_response = self.get_ai_response(command)
                        request.set_state("response_ready")
                        print(f"[{request_id}] RESPONSE_READY")
                        return ai_response, False
                    
                    return response, False
                else:
                    # Non-question commands - try AI first, then LLM-classified web search if needed
                    ai_response = None
                    try:
                        ai_response = self.get_ai_response(command)
                    except Exception as e:
                        print(f"AI response failed: {e}")
                    
                    if ai_response and len(ai_response.strip()) > 0:
                        request.set_state("response_ready")
                        print(f"[{request_id}] RESPONSE_READY")
                        return ai_response, False
                    else:
                        # Use LLM to determine if web search is needed for non-questions too
                        classification = self.classify_web_search(command)
                        
                        if classification["requires_web_search"] and classification["search_query"]:
                            request.set_state("searching")
                            print(f"[{request_id}] STATE_CHANGED - searching (operation=web_search)")
                            
                            response = self.search_and_answer(classification["search_query"])
                            return response, False
                    
                    return None, False
        
        except Exception as e:
            print(f"[{request_id}] REQUEST_FAILED - {e}")
            raise
        finally:
            # Complete the request lifecycle
            if not request.cancelled and not request.completed_at:
                self.request_manager.complete_request(request_id)

    def process_command(self, command):
        """Process the user's command, speak the response, and return response text."""
        response_text, is_exit = self.get_response_text(command)
        
        if response_text:
            self.speak(response_text)
        
        if is_exit:
            return "exit"
        
        return response_text
            
    def run(self):
        """Main loop for the Jarvis assistant (terminal mode - legacy)."""
        print("Starting Jarvis Assistant...")
        self.speak("Good day, Sir. JARVIS is now active. How may I assist you?")
        
        consecutive_failures = 0
        
        while True:
            try:
                command = self.listen()
                
                # Only process if we got a valid command
                if not command or len(command.strip()) == 0:
                    consecutive_failures += 1
                    
                    # After multiple failures, provide feedback to user
                    if consecutive_failures >= 3:
                        self.speak("I'm sorry, Sir. I didn't catch that. Please repeat your request.")
                        consecutive_failures = 0
                    continue
                
                # Reset failure counter on successful recognition
                consecutive_failures = 0
                
                command_lower = command.lower()
                
                # Check if user wants to exit - comprehensive shutdown detection
                if any(phrase in command_lower for phrase in [
                    "exit", "quit", "bye", "goodbye", 
                    "exit jarvis", "quit jarvis", "close jarvis",
                    "stop jarvis", "shut down jarvis"
                ]):
                    self.speak("Goodbye, Sir.")
                    break
                
                # Process the command and ensure we get a response
                result = self.process_command(command)
                
                # If process_command returned None (e.g., silence commands), continue listening
                if result == "exit":
                    break
                    
            except KeyboardInterrupt:
                print("\nInterrupted by user")
                self.speak("Goodbye, Sir.")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                self.speak("Apologies, Sir. I encountered an error. Please try again.")