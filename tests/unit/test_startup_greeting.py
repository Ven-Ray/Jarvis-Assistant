import sys
import os

# Add project root to path (parent of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jarvis import JarvisAssistant

j = JarvisAssistant()
print('Voice records dir:', j.voice_records_dir)

greeting_file = os.path.join(j.voice_records_dir, 'startup_greeting.mp3')
if os.path.exists(greeting_file):
    os.remove(greeting_file)
    print('Removed old cached file if it existed')
else:
    print('No existing cached file found')
