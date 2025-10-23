import whisper
import sounddevice as sd
import numpy as np
from pynput import keyboard
import tempfile
import wavio
import os
import sys
import queue
import threading

print("🔄 Loading Whisper model...")
model = whisper.load_model("base", device="cpu")

# 🔍 Pick your mic (try 1, 7, or 15)
mic_index = 15

try:
    # 🧠 Get default mic info
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
print("Press ESC to quit.\n")

# State variables
is_recording = False
audio_queue = queue.Queue()
recording_frames = []

def audio_callback(indata, frames, time, status):
    """Callback for audio stream"""
    if status:
        print(f"⚠️  Audio status: {status}")
    if is_recording:
        audio_queue.put(indata.copy())

def resample_audio(audio, orig_sr, target_sr=16000):
    """Resample audio to target sample rate"""
    if orig_sr == target_sr:
        return audio, target_sr
    
    duration = len(audio) / orig_sr
    target_length = int(duration * target_sr)
    resampled = np.interp(
        np.linspace(0, len(audio), target_length),
        np.arange(len(audio)),
        audio
    )
    return resampled, target_sr

def on_press(key):
    global is_recording, recording_frames
    
    try:
        if key == keyboard.Key.space and not is_recording:
            is_recording = True
            recording_frames = []
            
            # Clear queue
            while not audio_queue.empty():
                audio_queue.get()
            
            print("🎙️  Recording... (release SPACE to stop)")
            
    except AttributeError:
        pass

def on_release(key):
    global is_recording, recording_frames
    
    # Exit on ESC
    if key == keyboard.Key.esc:
        print("🛑 Exiting...")
        return False
    
    try:
        if key == keyboard.Key.space and is_recording:
            is_recording = False
            
            # Collect all queued audio
            while not audio_queue.empty():
                recording_frames.append(audio_queue.get())
            
            if not recording_frames:
                print("⚠️  No audio captured, try again.\n")
                return
            
            # Concatenate all frames
            audio_data = np.concatenate(recording_frames, axis=0).flatten()
            
            if len(audio_data) < samplerate * 0.5:
                print("⚠️  Recording too short, try again.\n")
                return
            
            print("🧠 Transcribing...")
            
            try:
                # Resample to 16kHz if needed
                audio_resampled, final_sr = resample_audio(audio_data, samplerate, 16000)
                
                # Normalize audio
                audio_resampled = audio_resampled / np.max(np.abs(audio_resampled) + 1e-8)
                
                # Write to temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    temp_path = f.name
                    wavio.write(temp_path, audio_resampled, final_sr, sampwidth=2)
                
                # Transcribe
                result = model.transcribe(temp_path, language="en", fp16=False)
                
                # Clean up temp file
                os.unlink(temp_path)
                
                # Display result
                text = result["text"].strip()
                if text:
                    print(f"✅ You said: {text}\n")
                else:
                    print("⚠️  No speech detected.\n")
                    
            except Exception as e:
                print(f"❌ Transcription error: {e}\n")
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
    except AttributeError:
        pass

# Try to start audio stream with error handling
try:
    print("🎯 Starting audio stream...")
    
    stream = sd.InputStream(
        device=mic_index,
        channels=1,
        samplerate=samplerate,
        callback=audio_callback,
        blocksize=2048,
        dtype='float32'
    )
    
    stream.start()
    print("✅ Audio stream active!\n")
    
except Exception as e:
    print(f"❌ Failed to start audio stream: {e}")
    print("\n💡 Troubleshooting tips:")
    print("1. Try a different mic_index value (check list above)")
    print("2. Close other apps using the microphone")
    print("3. Update your audio drivers")
    print("4. Try running as administrator")
    sys.exit(1)

# Start keyboard listener
print("🎯 Ready! Listening for keyboard input...\n")

try:
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
finally:
    # Clean up
    if 'stream' in locals():
        stream.stop()
        stream.close()

print("👋 Goodbye!")