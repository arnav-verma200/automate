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

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "ChromeAutomation")

driver = None
input_mode = None

def get_voice_input_continuous():
    r = sr.Recognizer()
    mic = sr.Microphone()
    
    print("Calibrating microphone for ambient noise... Please wait...")
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=2)
    print("Calibration complete! Listening continuously...")
    print("Press ESC to stop listening.\n")
    
    while True:
        if keyboard.is_pressed("esc"):
            print("\nStopping continuous listening...")
            return None
        
        try:
            with mic as source:
                print("🎤 Listening... (say 'Friday' to give a command)")
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                
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
            time.sleep(1)
            continue
        except Exception as e:
            print(f"❌ Error: {e}")
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
        print("Tip: Click 'Sign in' in the top right to stay logged in")
        return new_driver
    except Exception as e:
        print(f"Error creating driver: {e}")
        print("\nTrying alternative method...")
        
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
    global driver
    if driver:
        try:
            driver.quit()
        except:
            pass
        driver = None

def execute_command(command):
    global driver
    
    if command == "exit":
        cleanup_driver()
        print("Goodbye!")
        return False  
    
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
    
    elif command.startswith("open "):
        name = command.replace("open ", "", 1).strip()
        app_path = shutil.which(name)
        
        if app_path:
            os.startfile(app_path)
            print(f"✅ Opened {name}\n")
        
        elif name in ["chrome", "msedge", "firefox"]:
            os.system(f"start {name}")
            print(f"✅ Opened {name}\n")
        
        elif has_protocol(name):
            os.system(f"start {name}://")
            print(f"✅ Opened {name}\n")
        
        else:
            url = f"https://www.{name}.com" if "." not in name else f"https://{name}"
            
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
                
                if input_mode == "voice_continuous":
                    print("\n🎤 Listening... What do you want to play on YouTube?")
                    youtube_input = get_voice_input_continuous()
                    
                    if youtube_input:
                        youtube_input_lower = youtube_input.lower().strip()
                        
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
            
            else:
                webbrowser.open(url)
                print(f"✅ Opened {url}\n")
    
    else:
        print("❌ Unknown command. Available commands:")
        print("  search <query>  - Search on Google")
        print("  open <name>     - Open app or website")
        print("  exit            - Close program\n")
    
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
    
    print("\nCommands: search <query> | open <app/website> | exit")
    print("-" * 60)
    print("\nℹ️ First time? Sign in to Google when Chrome opens!")
    print("Your login will be saved for future sessions.\n")
    
    while True:
        if input_mode == "voice_continuous":
            voice_input = get_voice_input_continuous()
            
            if voice_input is None:  
                cleanup_driver()
                print("Goodbye!")
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

