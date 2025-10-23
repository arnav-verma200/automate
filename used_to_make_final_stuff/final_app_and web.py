import os
import webbrowser
import shutil
import winreg
import time
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

try:
  print("Browser Automation Script")
  print("Commands: search <query> | open <app/website> | exit")
  print("-" * 50)
  print("\nNote: First time? Sign in to Google when Chrome opens!")
  print("Your login will be saved for future sessions.\n")
  
  while True:
    command = input("\nCommand: ").lower().strip()
    
    if command == "exit":
      cleanup_driver()
      print("Goodbye!")
      break

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
            print(f"Searching Google for: {query}")
          except Exception as e:
            print(f"Error during search: {e}")
            cleanup_driver()
      else:
        print("No search query provided.")

    # Open applications or websites
    elif command.startswith("open "):
      name = command.replace("open ", "", 1).strip()
      app_path = shutil.which(name)
      
      # Open local apps
      if app_path:
        os.startfile(app_path)
        print(f"Opened {name}")
      
      # Open browsers directly
      elif name in ["chrome", "msedge", "firefox"]:
        os.system(f"start {name}")
        print(f"Opened {name}")
      
      # Open protocol apps
      elif has_protocol(name):
        os.system(f"start {name}://")
        print(f"Opened {name}")
      
      else:
        # Construct URL
        url = f"https://www.{name}.com" if "." not in name else f"https://{name}"
        
        # Selenium for YouTube
        if "youtube" in name:
          query = input("What do you want to play on YouTube? ").strip()
          
          if not driver:
            driver = create_driver()
          
          if driver:
            try:
              driver.get(url)
              print("Opened YouTube")
              
              if query:
                wait = WebDriverWait(driver, 10)
                search_box = wait.until(
                  EC.presence_of_element_located((By.NAME, "search_query"))
                )
                search_box.clear()
                search_box.send_keys(query)
                search_box.send_keys(Keys.RETURN)
                print(f"Searching for: {query}")
                
                # Wait for results and click first video
                time.sleep(3)
                try:
                  first_video = wait.until(
                    EC.element_to_be_clickable((By.XPATH, '(//a[@id="video-title"])[1]'))
                  )
                  video_title = first_video.get_attribute("title")
                  first_video.click()
                  print(f"Now playing: {video_title}")
                except:
                  print("Search results displayed")
              else:
                print("No query entered. Just opened YouTube.")
            except Exception as e:
              print(f"Error with YouTube: {e}")
              cleanup_driver()
        
        # Open other websites normally
        else:
          webbrowser.open(url)
          print(f"Opened {url}")
    
    else:
      print("Unknown command. Available commands:")
      print("  search <query>  - Search on Google")
      print("  open <name>     - Open app or website")
      print("  exit        - Close program")

except KeyboardInterrupt:
  print("\n\nExiting...")
  cleanup_driver()
except Exception as e:
  print(f"\nUnexpected error: {e}")
  cleanup_driver()