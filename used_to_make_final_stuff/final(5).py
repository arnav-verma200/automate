import os
import webbrowser
import shutil
import winreg
import time
import speech_recognition as sr
import keyboard
import pyttsx3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "ChromeAutomation")

driver = None
input_mode = None
whatsapp_logged_in = False

def speak(text):
  try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 175)
    engine.setProperty('volume', 0.9)
    print(text)
    engine.say(text)
    engine.runAndWait()
    engine.stop()
  except Exception as e:
    print(f"Speech error: {e}")

def get_voice_input_continuous(first_run=False):
  r = sr.Recognizer()
  mic = sr.Microphone()
  
  if first_run:
    print("Calibrating microphone for ambient noise... Please wait...")
    speak("Calibrating microphone, please wait")
    
    with mic as source:
      r.adjust_for_ambient_noise(source, duration=2)
    
    print("Calibration complete! Listening continuously. Press ESC to stop listening.")
    speak("Ready. I'm listening")
  
  while True:
    if keyboard.is_pressed("esc"):
      print("Stopping continuous listening...")
      speak("Goodbye")
      return None
    
    try:
      with mic as source:
        if first_run:
          r.adjust_for_ambient_noise(source, duration=0.5)
        print("🎤 Listening... say 'Friday' to give a command")
        audio = r.listen(source, timeout=5, phrase_time_limit=20)
        
        print("🔄 Processing...")
        text = r.recognize_google(audio)
        print(f"📢 Heard: {text}")
        
        if text.lower().strip().startswith("friday"):
          return text
        else:
          print("❌ Command ignored (didn't start with 'Friday')\n")
          
    except sr.WaitTimeoutError:
      continue
    except sr.UnknownValueError:
      print("❓ Could not understand, still listening...\n")
      continue
    except sr.RequestError as e:
      print(f"❌ Recognition service error: {e}")
      speak("Recognition service error")
      time.sleep(1)
      continue
    except Exception as e:
      print(f"❌ Error: {e}")
      speak("An error occurred")
      time.sleep(1)
      continue

def get_voice_input_button():
  r = sr.Recognizer()
  mic = sr.Microphone()
  
  max_retries = 3
  retry_count = 0
  
  while retry_count < max_retries:
    print("Hold SPACE to speak... release to stop and transcribe.")
    if retry_count > 0:
      print(f"Retry {retry_count}/{max_retries}")
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
            audio = r.listen(source, timeout=30, phrase_time_limit=20)
            duration = time.time() - start_time
            print(f"Recognizing ({duration:.1f}s)...")
            
            text = r.recognize_google(audio)
            print("You said:", text)
            return text
            
          except sr.WaitTimeoutError:
            print("No speech detected.")
            retry_count += 1
            break
          except sr.UnknownValueError:
            print("Could not understand. Please try again...")
            retry_count += 1
            break
          except sr.RequestError as e:
            print(f"Recognition service error: {e}")
            return None
          finally:
            while keyboard.is_pressed("space"):
              time.sleep(0.01)
  
  print(f"Failed after {max_retries} attempts.")
  return None

def has_protocol(name):
  try:
    key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{name}")
    try:
      winreg.QueryValueEx(key, "URL Protocol")
      winreg.CloseKey(key)
      return True
    except:
      winreg.CloseKey(key)
      return False
  except:
    return False

def create_driver():
  options = Options()
  options.binary_location = CHROME_PATH
  
  if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)
  
  options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
  options.add_argument("--profile-directory=Default")
  options.add_argument("--remote-allow-origins=*")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-gpu")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("--disable-software-rasterizer")
  options.add_argument("--disable-blink-features=AutomationControlled")
  options.add_argument("--start-maximized")
  options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
  options.add_experimental_option("useAutomationExtension", False)
  
  try:
    new_driver = webdriver.Chrome(
      service=Service(ChromeDriverManager().install()), 
      options=options
    )
    print("Chrome opened successfully!")
    return new_driver
  except Exception as e:
    print(f"Error creating driver: {e}. Trying alternative method...")
    
    try:
      options2 = Options()
      options2.binary_location = CHROME_PATH
      options2.add_argument("--remote-allow-origins=*")
      options2.add_argument("--no-sandbox")
      options2.add_argument("--disable-dev-shm-usage")
      options2.add_argument("--start-maximized")
      options2.add_experimental_option('excludeSwitches', ['enable-logging'])
      
      new_driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=options2
      )
      print("Chrome opened (temporary session)")
      return new_driver
    except Exception as e2:
      print(f"Failed to open Chrome: {e2}")
      if input_mode == "voice_continuous":
        speak("Failed to open Chrome")
      return None

def cleanup_driver():
  global driver, whatsapp_logged_in
  if driver:
    try:
      driver.quit()
    except:
      pass
    driver = None
    whatsapp_logged_in = False

def send_whatsapp_message(contact, message):
  """Send WhatsApp message via WhatsApp Web - Always clicks first search result"""
  global driver, whatsapp_logged_in
  
  if not driver:
    driver = create_driver()
  
  if driver:
    try:
      # Open WhatsApp Web if not already there
      if not whatsapp_logged_in:
        driver.get("https://web.whatsapp.com")
        msg = "📱 Opening WhatsApp Web..."
        if input_mode == "voice_continuous":
          speak("Opening WhatsApp Web")
        else:
          print(msg)
        
        wait = WebDriverWait(driver, 60)
        try:
          wait.until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
          )
          whatsapp_logged_in = True
          msg = "✅ WhatsApp Web logged in successfully!"
          if input_mode == "voice_continuous":
            speak("WhatsApp logged in")
          else:
            print(msg)
        except Exception:
          msg = "⏳ Please scan the QR code on WhatsApp Web to continue..."
          if input_mode == "voice_continuous":
            speak("Please scan QR code")
          else:
            print(msg)
          
          wait = WebDriverWait(driver, 120)
          wait.until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
          )
          whatsapp_logged_in = True
          msg = "✅ QR code scanned! WhatsApp ready!"
          if input_mode == "voice_continuous":
            speak("WhatsApp ready")
          else:
            print(msg)
      
      # Now send the message
      wait = WebDriverWait(driver, 15)
      
      # Find and click search box
      search_box = wait.until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
      )
      search_box.click()
      time.sleep(0.5)
      
      # Clear any existing search
      search_box.send_keys(Keys.CONTROL + "a")
      search_box.send_keys(Keys.BACKSPACE)
      time.sleep(0.3)
      
      # Type contact name
      search_box.send_keys(contact)
      msg = f"🔍 Searching for contact: {contact}"
      if input_mode == "voice_continuous":
        speak(f"Searching for {contact}")
      else:
        print(msg)
      time.sleep(2.5)  # Wait for search results to load
      
      # ALWAYS click the first result - Try multiple strategies
      contact_clicked = False
      
      # Strategy 1: Click first visible chat span with title
      try:
        first_result = wait.until(
          EC.element_to_be_clickable((By.XPATH, '(//span[@title])[1]'))
        )
        first_result.click()
        contact_clicked = True
        msg = f"✅ Selected first result for '{contact}'"
        if input_mode == "voice_continuous":
          speak("Contact selected")
        else:
          print(msg)
      except Exception:
        pass
      
      # Strategy 2: Click using the specific structure
      if not contact_clicked:
        try:
          first_result = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//div[@id="pane-side"]//div[@role="listitem"][1]'))
          )
          first_result.click()
          contact_clicked = True
          msg = f"✅ Selected first result for '{contact}'"
          if input_mode == "voice_continuous":
            speak("Contact selected")
          else:
            print(msg)
        except Exception:
          pass
      
      # Strategy 3: Press DOWN arrow and ENTER (most reliable!)
      if not contact_clicked:
        try:
          search_box.send_keys(Keys.DOWN)
          time.sleep(0.3)
          search_box.send_keys(Keys.RETURN)
          contact_clicked = True
          msg = f"✅ Selected first result for '{contact}'"
          if input_mode == "voice_continuous":
            speak("Contact selected")
          else:
            print(msg)
        except Exception:
          pass
      
      # If nothing worked
      if not contact_clicked:
        msg = f"❌ No search results found for '{contact}'\n"
        if input_mode == "voice_continuous":
          speak(f"No results for {contact}")
        else:
          print(msg)
        # Clear the search
        search_box.send_keys(Keys.ESCAPE)
        return
      
      time.sleep(1)
      
      # Find message input box and send message
      try:
        message_box = wait.until(
          EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
        )
      except Exception:
        # Alternative: Try finding by role
        message_box = wait.until(
          EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"][@contenteditable="true"]'))
        )
      
      message_box.click()
      time.sleep(0.3)
      
      # Type and send message
      message_box.send_keys(message)
      time.sleep(0.5)
      message_box.send_keys(Keys.RETURN)
      
      msg = f"✅ Message sent: '{message}'\n"
      if input_mode == "voice_continuous":
        speak("Message sent")
      else:
        print(msg)
        
    except Exception as e:
      msg = f"❌ Error sending WhatsApp message: {e}\n"
      if input_mode == "voice_continuous":
        speak("Error sending WhatsApp message")
      else:
        print(msg)
      whatsapp_logged_in = False

def play_youtube_video(query):
  """Play a YouTube video with the given query"""
  global driver, whatsapp_logged_in
  
  if not driver:
    driver = create_driver()
  
  if driver:
    try:
      driver.get("https://www.youtube.com")
      whatsapp_logged_in = False  # Reset WhatsApp status when navigating away
      
      msg = f"✅ Opening YouTube to play: {query}"
      if input_mode == "voice_continuous":
        speak(msg)
      else:
        print(msg)
      
      wait = WebDriverWait(driver, 10)
      search_box = wait.until(
        EC.presence_of_element_located((By.NAME, "search_query"))
      )
      search_box.clear()
      search_box.send_keys(query)
      search_box.send_keys(Keys.RETURN)
      
      time.sleep(3)
      try:
        first_video = wait.until(
          EC.element_to_be_clickable((By.XPATH, '(//a[@id="video-title"])[1]'))
        )
        video_title = first_video.get_attribute("title")
        first_video.click()
        msg = f"▶️ Now playing: {video_title}\n"
        if input_mode == "voice_continuous":
          speak(f"Now playing {video_title}")
        else:
          print(msg)
      except Exception:
        msg = "✅ Search results displayed\n"
        if input_mode == "voice_continuous":
          speak(msg)
        else:
          print(msg)
    except Exception as e:
      msg = f"❌ Error playing video: {e}\n"
      if input_mode == "voice_continuous":
        speak(msg)
      else:
        print(msg)
      cleanup_driver()

def get_user_input(prompt_text):
  """Get input from user based on current input mode"""
  if input_mode == "voice_continuous":
    speak(prompt_text)
    print(f"\n{prompt_text}")
    print("🎤 Say 'Friday' followed by your response...")
    
    voice_input = get_voice_input_continuous(first_run=False)
    if voice_input is None:
      return None
    
    response = voice_input.lower().replace("friday", "", 1).strip()
    print(f"📢 You said: {response}")
    return response
  
  elif input_mode == "voice_button":
    speak(prompt_text)
    print(f"\n{prompt_text}")
    print("Hold SPACE and say 'Friday' followed by your response...")
    
    voice_input = get_voice_input_button()
    if voice_input:
      voice_input_lower = voice_input.lower().strip()
      if voice_input_lower.startswith("friday"):
        response = voice_input_lower.replace("friday", "", 1).strip()
        print(f"📢 You said: {response}")
        return response
      else:
        print("❌ Response ignored. Please start with 'Friday'")
        return None
    return None
  
  else:  # typing mode
    return input(f"{prompt_text}: ").strip()

def execute_command(command):
  global driver, whatsapp_logged_in
  
  if command == "exit":
    cleanup_driver()
    msg = "Goodbye!"
    if input_mode == "voice_continuous":
      speak(msg)
    else:
      print(msg)
    return False  
  
  elif command.startswith("message"):
    # Parse: "message dhruv" - extract contact name
    rest = command.replace("message", "", 1).strip()
    
    if rest:
      contact = rest
      
      # Ask for message
      msg = f"What message do you want to send to {contact}?"
      if input_mode == "voice_continuous":
        speak(msg)
      print(msg)
      
      message = get_user_input("Enter message")
      
      if not message:
        msg = "❌ No message provided. Message cancelled.\n"
        if input_mode == "voice_continuous":
          speak("Message cancelled")
        else:
          print(msg)
        return True
      
      # Send the message - will automatically select first search result
      send_whatsapp_message(contact, message)
    else:
      msg = "❌ No contact provided. Format: message <contact>\n"
      if input_mode == "voice_continuous":
        speak("No contact provided")
      else:
        print(msg)
  
  elif command.startswith("play "):
    query = command.replace("play ", "", 1).strip()
    if query:
      play_youtube_video(query)
    else:
      msg = "❌ No video name provided.\n"
      if input_mode == "voice_continuous":
        speak(msg)
      else:
        print(msg)
  
  elif command.startswith("search "):
    query = command.replace("search ", "", 1).strip()
    if query:
      if not driver:
        driver = create_driver()
      
      if driver:
        try:
          driver.get("https://www.google.com")
          whatsapp_logged_in = False  # Reset WhatsApp status
          
          wait = WebDriverWait(driver, 10)
          search_box = wait.until(
            EC.presence_of_element_located((By.NAME, "q"))
          )
          search_box.clear()
          search_box.send_keys(query)
          search_box.send_keys(Keys.RETURN)
          msg = f"✅ Searching Google for: {query}\n"
          if input_mode == "voice_continuous":
            speak(msg)
          else:
            print(msg)
        except Exception as e:
          msg = f"❌ Error during search: {e}\n"
          if input_mode == "voice_continuous":
            speak(msg)
          else:
            print(msg)
          cleanup_driver()
    else:
      msg = "❌ No search query provided.\n"
      if input_mode == "voice_continuous":
        speak(msg)
      else:
        print(msg)
  
  elif command.startswith("open "):
    name = command.replace("open ", "", 1).strip()
    app_path = shutil.which(name)
    
    if app_path:
      os.startfile(app_path)
      msg = f"✅ Opened {name}\n"
      if input_mode == "voice_continuous":
        speak(msg)
      else:
        print(msg)
    
    elif name in ["chrome", "msedge", "firefox"]:
      os.system(f"start {name}")
      msg = f"✅ Opened {name}\n"
      if input_mode == "voice_continuous":
        speak(msg)
      else:
        print(msg)
    
    elif has_protocol(name):
      os.system(f"start {name}://")
      msg = f"✅ Opened {name}\n"
      if input_mode == "voice_continuous":
        speak(msg)
      else:
        print(msg)
    
    elif "youtube" in name:
      if not driver:
        driver = create_driver()
      
      if driver:
        try:
          driver.get("https://www.youtube.com")
          whatsapp_logged_in = False  # Reset WhatsApp status
          
          msg = "✅ Opened YouTube\n"
          if input_mode == "voice_continuous":
            speak("Opened YouTube")
          else:
            print(msg)
        except Exception as e:
          msg = f"❌ Error opening YouTube: {e}\n"
          if input_mode == "voice_continuous":
            speak(msg)
          else:
            print(msg)
          cleanup_driver()
    
    elif "whatsapp" in name:
      if not driver:
        driver = create_driver()
      
      if driver:
        try:
          driver.get("https://web.whatsapp.com")
          whatsapp_logged_in = False  # Will need to verify login
          
          msg = "✅ Opening WhatsApp Web\n"
          if input_mode == "voice_continuous":
            speak("Opening WhatsApp")
          else:
            print(msg)
        except Exception as e:
          msg = f"❌ Error opening WhatsApp: {e}\n"
          if input_mode == "voice_continuous":
            speak(msg)
          else:
            print(msg)
          cleanup_driver()
    
    else:
      url = f"https://www.{name}.com" if "." not in name else f"https://{name}"
      webbrowser.open(url)
      msg = f"✅ Opened {url}\n"
      if input_mode == "voice_continuous":
        speak(msg)
      else:
        print(msg)
  
  else:
    msg = "❌ Unknown command. Available commands: play <video>, search <query>, open <name>, message <contact>, exit\n"
    if input_mode == "voice_continuous":
      speak(msg)
    else:
      print(msg)
  
  return True 

try:
  print("=" * 60)
  print("🤖 FRIDAY - Voice Controlled Browser Automation")
  print("=" * 60)
  print("\nSelect Input Mode:")
  print("1 - Continuous Voice Control (Always Listening)")
  print("2 - Button Voice Control (Press SPACE to talk)")
  print("3 - Typing")
  print("-" * 60)
  
  while True:
    mode_choice = input("\nEnter your choice (1, 2, or 3): ").strip()
    if mode_choice == "1":
      input_mode = "voice_continuous"
      print("\n✅ Continuous Voice Mode Activated!")
      print("🎤 I'm always listening for 'Friday' commands")
      print("⚠️ Press ESC anytime to stop\n")
      break
    elif mode_choice == "2":
      input_mode = "voice_button"
      print("\n✅ Button Voice Mode Activated!")
      print("🎤 Hold SPACE to speak your commands")
      print("⚠️ Start every command with 'Friday'\n")
      break
    elif mode_choice == "3":
      input_mode = "typing"
      print("\n✅ Typing Mode Activated!\n")
      break
    else:
      print("❌ Invalid choice. Please enter 1, 2, or 3.")
  
  print("\nCommands:")
  print("  • message <contact>      - Send WhatsApp message (then enter text)")
  print("  • play <video>           - Play YouTube video")
  print("  • search <query>         - Google search")
  print("  • open <app/website>     - Open application or website")
  print("  • exit                   - Exit program")
  print("-" * 60)
  print("\nℹ️ First time? Sign in to Google & WhatsApp when Chrome opens!")
  print("Your login will be saved for future sessions.")
  print("\n💡 TIP: WhatsApp will ALWAYS message the first person in search results!\n")
  
  first_voice_command = True
  
  while True:
    if input_mode == "voice_continuous":
      voice_input = get_voice_input_continuous(first_run=first_voice_command)
      first_voice_command = False
      
      if voice_input is None:  
        cleanup_driver()
        break
      
      command = voice_input.lower().replace("friday", "", 1).strip()
      print(f"⚡ Executing: {command}\n")
      
    elif input_mode == "voice_button":
      print("\n[Voice Mode - Say 'Friday' first]")
      voice_input = get_voice_input_button()
      
      if voice_input:
        voice_input_lower = voice_input.lower().strip()
        
        if voice_input_lower.startswith("friday"):
          command = voice_input_lower.replace("friday", "", 1).strip()
          print(f"\n⚡ Executing: {command}\n")
        else:
          print("❌ Command ignored. Please start with 'Friday'")
          continue
      else:
        print("❌ No voice command received.")
        continue
    else:
      command = input("\nCommand: ").lower().strip()
    
    should_continue = execute_command(command)
    if not should_continue:
      break

except KeyboardInterrupt:
  print("\n\n⚠️ Interrupted by user...")
  cleanup_driver()
except Exception as e:
  print(f"\n❌ Unexpected error: {e}")
  cleanup_driver()
