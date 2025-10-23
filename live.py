import os
import webbrowser
import shutil
import winreg
import time
import speech_recognition as sr
import keyboard
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Path to Chrome executable
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
# Path to your Chrome user data folder (for persistent login)
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "ChromeAutomation")

# Global driver variable
driver = None
input_mode = None

def get_voice_input_continuous():
    """Continuously listen for voice commands without button press"""
    r = sr.Recognizer()
    mic = sr.Microphone()
    
    # Adjust for ambient noise once at the start
    print("Calibrating microphone for ambient noise... Please wait...")
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=2)
    print("Calibration complete! Listening continuously...")
    print("Press ESC to stop listening.\n")
    
    while True:
        # Check for ESC key to stop
        if keyboard.is_pressed("esc"):
            print("\nStopping continuous listening...")
            return None
        
        try:
            with mic as source:
                print("🎤 Listening... (say 'Friday' to give a command)")
                # Listen with a timeout
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                
                print("🔄 Processing...")
                text = r.recognize_google(audio)
                print(f"📢 Heard: {text}")
                
                # Check if command starts with "Friday"
                if text.lower().strip().startswith("friday"):
                    return text
                else:
                    print("❌ Command ignored (didn't start with 'Friday')\n")
                    
        except sr.WaitTimeoutError:
            # Normal timeout, just continue listening
            continue
        except sr.UnknownValueError:
            print("❓ Could not understand, still listening...\n")
            continue
        except sr.RequestError as e:
            print(f"❌ Recognition service error: {e}")
            time.sleep(1)
            continue
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)
            continue

def get_voice_input_button():
    """Original button-press voice input"""
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
                        audio = r.listen(source, timeout=30, phrase_time_limit=10)
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
    """Check if a protocol handler exists in Windows registry"""
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
    """Create and return a Chrome WebDriver instance"""
    options = Options()
    options.binary_location = CHROME_PATH
    
    # Create the user data directory if it doesn't exist
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)
    
    # Use a dedicated profile for automation (keeps you logged in)
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
        print("Tip: Click 'Sign in' in the top right to stay logged in")
        return new_driver
    except Exception as e:
        print(f"Error creating driver: {e}")
        print("\nTrying alternative method...")
        
        # Try without custom profile as fallback
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
            print("Chrome opened (temporary session - won't save login)")
            return new_driver
        except Exception as e2:
            print(f"Still failed: {e2}")
            return None

def cleanup_driver():
    """Safely close the driver"""
    global driver
    if driver:
        try:
            driver.quit()
        except:
            pass
        driver = None

def execute_command(command):
    """Execute a command (used by both voice and typing modes)"""
    global driver
    
    if command == "exit":
        cleanup_driver()
        print("Goodbye!")
        return False  # Signal to exit main loop
    
    # Google search
    elif command.startswith("search "):
        query = command.replace("search ", "", 1).strip()
        if query:
            if not driver:
                driver = create_driver()
            
            if driver:
                try:
                    driver.get("https://www.google.com")
                    wait = WebDriverWait(driver, 10)
                    search_box = wait.until(
                        EC.presence_of_element_located((By.NAME, "q"))
                    )
                    search_box.clear()
                    search_box.send_keys(query)
                    search_box.send_keys(Keys.RETURN)
                    print(f"✅ Searching Google for: {query}\n")
                except Exception as e:
                    print(f"❌ Error during search: {e}\n")
                    cleanup_driver()
        else:
            print("❌ No search query provided.\n")
    
    # Open applications or websites
    elif command.startswith("open "):
        name = command.replace("open ", "", 1).strip()
        app_path = shutil.which(name)
        
        # Open local apps
        if app_path:
            os.startfile(app_path)
            print(f"✅ Opened {name}\n")
        
        # Open browsers directly
        elif name in ["chrome", "msedge", "firefox"]:
            os.system(f"start {name}")
            print(f"✅ Opened {name}\n")
        
        # Open protocol apps
        elif has_protocol(name):
            os.system(f"start {name}://")
            print(f"✅ Opened {name}\n")
        
        else:
            # Construct URL
            url = f"https://www.{name}.com" if "." not in name else f"https://{name}"
            
            # Selenium for YouTube
            if "youtube" in name:
                if not driver:
                    driver = create_driver()
                
                if driver:
                    try:
                        driver.get(url)
                        print("✅ Opened YouTube")
                    except Exception as e:
                        print(f"❌ Error opening YouTube: {e}\n")
                        cleanup_driver()
                        return True
                
                # Get YouTube search query based on mode
                if input_mode == "voice_continuous":
                    print("\n🎤 Listening... What do you want to play on YouTube?")
                    youtube_input = get_voice_input_continuous()
                    
                    if youtube_input:
                        youtube_input_lower = youtube_input.lower().strip()
                        
                        # Check if starts with "friday"
                        if youtube_input_lower.startswith("friday"):
                            query = youtube_input_lower.replace("friday", "", 1).strip()
                            print(f"\n🔍 Searching for: {query}")
                        else:
                            print("❌ Command ignored. Please start with 'Friday'")
                            query = ""
                    else:
                        query = ""
                elif input_mode == "voice_button":
                    print("\n🎤 What do you want to play on YouTube? (Say 'Friday' first)")
                    youtube_input = get_voice_input_button()
                    
                    if youtube_input:
                        youtube_input_lower = youtube_input.lower().strip()
                        
                        # Check if starts with "friday"
                        if youtube_input_lower.startswith("friday"):
                            query = youtube_input_lower.replace("friday", "", 1).strip()
                            print(f"\n🔍 Searching for: {query}")
                        else:
                            print("❌ Command ignored. Please start with 'Friday'")
                            query = ""
                    else:
                        query = ""
                else:
                    query = input("What do you want to play on YouTube?: ").strip()
                
                if driver and query:
                    try:
                        wait = WebDriverWait(driver, 10)
                        search_box = wait.until(
                            EC.presence_of_element_located((By.NAME, "search_query"))
                        )
                        search_box.clear()
                        search_box.send_keys(query)
                        search_box.send_keys(Keys.RETURN)
                        print(f"🔍 Searching for: {query}")

                        # Wait for results and click first video
                        time.sleep(3)
                        try:
                            first_video = wait.until(
                                EC.element_to_be_clickable((By.XPATH, '(//a[@id="video-title"])[1]'))
                            )
                            video_title = first_video.get_attribute("title")
                            first_video.click()
                            print(f"▶️ Now playing: {video_title}\n")
                        except Exception:
                            print("✅ Search results displayed\n")
                    except Exception as e:
                        print(f"❌ Error with YouTube: {e}\n")
                        cleanup_driver()
                else:
                    print("ℹ️ No query entered. Just opened YouTube.\n")
            
            # Open other websites normally
            else:
                webbrowser.open(url)
                print(f"✅ Opened {url}\n")
    
    else:
        print("❌ Unknown command. Available commands:")
        print("  search <query>  - Search on Google")
        print("  open <name>     - Open app or website")
        print("  exit            - Close program\n")
    
    return True  # Continue main loop

try:
    print("=" * 60)
    print("🤖 FRIDAY - Voice Controlled Browser Automation")
    print("=" * 60)
    print("\nSelect Input Mode:")
    print("1 - Continuous Voice Control (Always Listening)")
    print("2 - Button Voice Control (Press SPACE to talk)")
    print("3 - Typing")
    print("-" * 60)
    
    # Get input mode selection
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
    
    print("\nCommands: search <query> | open <app/website> | exit")
    print("-" * 60)
    print("\nℹ️ First time? Sign in to Google when Chrome opens!")
    print("Your login will be saved for future sessions.\n")
    
    while True:
        # Get command based on selected mode
        if input_mode == "voice_continuous":
            voice_input = get_voice_input_continuous()
            
            if voice_input is None:  # ESC was pressed
                cleanup_driver()
                print("Goodbye!")
                break
            
            # Remove "friday" from the beginning
            command = voice_input.lower().replace("friday", "", 1).strip()
            print(f"⚡ Executing: {command}\n")
            
        elif input_mode == "voice_button":
            print("\n[Voice Mode - Say 'Friday' first]")
            voice_input = get_voice_input_button()
            
            if voice_input:
                voice_input_lower = voice_input.lower().strip()
                
                # Check if command starts with "friday"
                if voice_input_lower.startswith("friday"):
                    # Remove "friday" from the beginning
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
        
        # Execute the command
        should_continue = execute_command(command)
        if not should_continue:
            break

except KeyboardInterrupt:
    print("\n\n⚠️ Interrupted by user...")
    cleanup_driver()
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    cleanup_driver()

