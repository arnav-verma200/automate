import whisper
import sounddevice as sd
import numpy as np
from pynput import keyboard
import threading
import sys
from collections import deque

print("🔄 Loading Whisper model...")
# Use 'small' model for best Hinglish accuracy
model = whisper.load_model("small", device="cpu")

# 🔍 Pick your mic
mic_index = 15

try:
    device_info = sd.query_devices(mic_index, 'input')
    samplerate = int(device_info['default_samplerate'])
    
    print(f"✅ Using input device index {mic_index}")
    print(f"📊 Sample rate: {samplerate} Hz")
    print(f"🎤 Device: {device_info['name']}")
except Exception as e:
    print(f"❌ Error: Could not access mic index {mic_index}")
    print(f"\nAvailable devices:")
    print(sd.query_devices())
    sys.exit(1)

print("\n🎤 Hold SPACE to record... release to stop and transcribe.")
print("🌏 Perfect for Hinglish - transcribes everything in Roman script")
print("Press ESC to quit.\n")

# State variables
is_recording = False
recording_frames = deque()

def audio_callback(indata, frames, time, status):
    """Callback for audio stream"""
    if is_recording:
        recording_frames.append(indata[:, 0].astype(np.float32).copy())

def transcribe_async(audio_data):
    """Transcribe in background thread"""
    try:
        # Resample to 16kHz inline
        if samplerate != 16000:
            duration = len(audio_data) / samplerate
            target_length = int(duration * 16000)
            audio_data = np.interp(
                np.linspace(0, len(audio_data), target_length),
                np.arange(len(audio_data)),
                audio_data
            )
        
        # Normalize
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        
        # Transcribe with auto language detection
        # Whisper handles Hinglish naturally and outputs in Roman script
        result = model.transcribe(
            audio_data,
            language=None,  # Auto-detect
            fp16=False,
            condition_on_previous_text=False,
            temperature=0.0,
            best_of=1,
            beam_size=2,
            patience=1.0,
            task="transcribe"  # Keep original language, don't translate
        )
        
        text = result["text"].strip()
        
        if text:
            print(f"✅ You said: {text}\n")
        else:
            print("⚠️  No speech detected.\n")
            
    except Exception as e:
        print(f"❌ Transcription error: {e}\n")

def on_press(key):
    global is_recording
    
    try:
        if key == keyboard.Key.space and not is_recording:
            is_recording = True
            recording_frames.clear()
            print("🎙️  Recording... (release SPACE to stop)")
    except AttributeError:
        pass

def on_release(key):
    global is_recording
    
    if key == keyboard.Key.esc:
        print("🛑 Exiting...")
        return False
    
    try:
        if key == keyboard.Key.space and is_recording:
            is_recording = False
            
            if not recording_frames:
                print("⚠️  No audio captured, try again.\n")
                return
            
            audio_data = np.concatenate(list(recording_frames))
            
            if len(audio_data) < samplerate * 0.3:
                print("⚠️  Recording too short, try again.\n")
                return
            
            print("🧠 Transcribing...")
            
            # Transcribe in background
            thread = threading.Thread(target=transcribe_async, args=(audio_data,), daemon=True)
            thread.start()
                    
    except AttributeError:
        pass

# Start audio stream
try:
    print("🎯 Starting audio stream...")
    
    stream = sd.InputStream(
        device=mic_index,
        channels=1,
        samplerate=samplerate,
        callback=audio_callback,
        blocksize=1024,
        dtype='float32'
    )
    
    stream.start()
    print("✅ Audio stream active!\n")
    
except Exception as e:
    print(f"❌ Failed to start audio stream: {e}")
    sys.exit(1)

print("🎯 Ready! Press SPACE to record...\n")

try:
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
finally:
    if 'stream' in locals():
        stream.stop()
        stream.close()

print("👋 Goodbye!")