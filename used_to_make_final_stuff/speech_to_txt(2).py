import speech_recognition as sr
import keyboard
import time

def get_voice_input():
  r = sr.Recognizer()
  mic = sr.Microphone()
  
  print("Hold SPACE to speak... release to stop and transcribe.")
  print("Press ESC to cancel.\n")
  
  while True:
    time.sleep(0.01)
    
    if keyboard.is_pressed("esc"):
      print("Cancelled.")
      return None

    if keyboard.is_pressed("space"):
      print("Listening...")
      with mic as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        start_time = time.time()
        try:
          audio = r.listen(source, timeout=30, phrase_time_limit=10)
          duration = time.time() - start_time
          print(f"Recognizing ({duration:.1f}s)...")
          
          text = r.recognize_google(audio)
          print("You said:", text)
          return text
          
        except sr.WaitTimeoutError:
          print("No speech detected.")
          return None
        except sr.UnknownValueError:
          print("Could not understand.")
          return None
        except sr.RequestError as e:
          print(f"Recognition service error: {e}")
          return None
        finally:
          while keyboard.is_pressed("space"):
            time.sleep(0.01)

get_voice_input()