#!/usr/bin/env python3
"""
Voice Generation Application - Command Line Interface

Usage:
    python cli.py save --name "Jarvis" --file "Jarvis.mp3" [--language en] [--consent]
    python cli.py list
    python cli.py generate --voice "Jarvis" --text "Hello, world!" [--output output.wav]
    python cli.py delete --voice "Jarvis"
"""

import argparse
import sys
import os

# Add parent directory to path for imports when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice_gen import (
    validate_audio_file, analyze_audio_quality,
    save_voice, list_voices, get_voice, delete_voice, select_voice,
    generate_voice, is_cuda_available
)


def cmd_save(args):
    """Save a reference voice."""
    print(f"Validating audio file: {args.file}")
    
    # Validate the audio file
    validation = validate_audio_file(args.file)
    
    if not validation["valid"]:
        print(f"Validation failed: {validation['error']}")
        return 1
    
    print("Audio file is valid.")
    
    # Analyze quality and show warnings
    analysis = analyze_audio_quality(args.file)
    
    for warning in analysis["warnings"]:
        print(f"Warning: {warning}")
    
    # Require explicit consent confirmation
    if not args.consent:
        print("\nConsent required. Please confirm:")
        print("I confirm that I own this recording or have permission from the speaker")
        print("to clone and generate speech with this voice.")
        print("\nUse --consent flag to confirm.")
        return 1
    
    # Save the voice
    try:
        result = save_voice(
            display_name=args.name,
            original_file_path=args.file,
            consent_confirmed=True,
            language=args.language
        )
        
        print(f"\nVoice saved successfully!")
        print(f"  Display name: {result['display_name']}")
        print(f"  Stored at: {result['stored_path']}")
        print(f"  SHA-256: {result['sha256_hash'][:16]}...")
        
    except Exception as e:
        print(f"Error saving voice: {e}")
        return 1
    
    return 0


def cmd_list(args):
    """List all saved voices."""
    voices = list_voices()
    
    if not voices:
        print("No saved voices found.")
        return 0
    
    print(f"Saved voices ({len(voices)}):")
    print("-" * 60)
    
    for voice in voices:
        print(f"  Name: {voice['display_name']}")
        print(f"  Language: {voice['language']}")
        print(f"  Created: {voice['creation_timestamp'][:19]}")
        print(f"  Hash: {voice['sha256_hash'][:16]}...")
        print("-" * 60)
    
    return 0


def cmd_generate(args):
    """Generate speech using a saved voice."""
    # Get the reference audio path
    try:
        reference_path = select_voice(args.voice)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    print(f"Using voice: {args.voice}")
    print(f"Reference audio: {reference_path}")
    
    # Generate speech
    try:
        output = generate_voice(
            text=args.text,
            reference_audio_path=reference_path,
            output_path=args.output,
            language=args.language
        )
        
        print(f"\nSpeech generated successfully!")
        print(f"  Output: {output}")
        
    except Exception as e:
        print(f"Error generating speech: {e}")
        return 1
    
    return 0


def cmd_delete(args):
    """Delete a saved voice."""
    if delete_voice(args.voice):
        print(f"Voice '{args.voice}' deleted successfully.")
    else:
        print(f"Voice '{args.voice}' not found.")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Voice Generation Application - Clone and generate speech with reference voices."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Save command
    save_parser = subparsers.add_parser("save", help="Save a reference voice")
    save_parser.add_argument("--name", required=True, help="Display name for the voice (e.g., 'Jarvis')")
    save_parser.add_argument("--file", required=True, help="Path to reference audio file")
    save_parser.add_argument("--language", default="en", help="Language code (default: en)")
    save_parser.add_argument(
        "--consent", action="store_true",
        help="Confirm consent: 'I confirm that I own this recording or have permission from the speaker to clone and generate speech with this voice.'"
    )
    
    # List command
    subparsers.add_parser("list", help="List all saved voices")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate speech using a saved voice")
    gen_parser.add_argument("--voice", required=True, help="Name of the voice to use")
    gen_parser.add_argument("--text", required=True, help="Text to synthesize")
    gen_parser.add_argument("--output", default="output.wav", help="Output file path (default: output.wav)")
    gen_parser.add_argument("--language", default="en", help="Language code (default: en)")
    
    # Delete command
    del_parser = subparsers.add_parser("delete", help="Delete a saved voice")
    del_parser.add_argument("--voice", required=True, help="Name of the voice to delete")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch command
    commands = {
        "save": cmd_save,
        "list": cmd_list,
        "generate": cmd_generate,
        "delete": cmd_delete
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())