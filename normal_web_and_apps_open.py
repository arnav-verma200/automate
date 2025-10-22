import os
import webbrowser
import shutil
import winreg


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


while True:
    command = input("Command: ").lower().strip()
    
    if command.startswith("open "):
        name = command.replace("open ", "").strip()
        app_path = shutil.which(name)
        
        if app_path:
            os.startfile(app_path)
            print(f"Opened {name}")
            
        elif name in ["chrome", "msedge", "firefox"]:
            os.system(f"start {name}")
            print(f"Opened {name}")
            
        elif has_protocol(name):
            os.system(f"start {name}://")
            print(f"Opened {name}")
            
        else:
            url = f"https://www.{name}.com" if "." not in name else f"https://{name}"
            webbrowser.open(url)
            print(f"Opened {url}")