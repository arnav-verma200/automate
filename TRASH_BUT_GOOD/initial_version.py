import os
import webbrowser
import shutil

while True:
    command = input("Command: ").lower().strip()
    
    if command == "exit":
        break
    
    if command.startswith("open "):
        name = command.replace("open ", "").strip()
        
        #PATH
        app_path = shutil.which(name)
        if app_path:
            os.startfile(app_path)
            print(f"Opened {name}")
            continue
        
        #Browsers dynamically
        browsers = ["chrome", "msedge", "firefox"]
        if name in browsers:
            os.system(f"start {name}")
            print(f"Opened {name}")
            continue
        
        #Website
        if "." not in name:
            url = f"https://www.{name}.com"
        else:
            url = f"https://{name}"
        webbrowser.open(url)
        print(f"Opened {url}")
