import os
import xbmc
import xbmcgui

LOGIN_FILE = xbmc.translatePath('special://home/userdata/profiles/{}/login.txt'.format(xbmc.getInfoLabel('System.ProfileName')))

# Function to prompt for username and password and save to login.txt
def save_login():
    username = ""
    password = ""
    
    if os.path.exists(LOGIN_FILE):
        choice = xbmcgui.Dialog().yesno("Login Found", "A login file already exists. Do you want to modify it?")
        if not choice:
            return
        
        # Read existing credentials
        with open(LOGIN_FILE, "r") as file:
            lines = file.readlines()
            if len(lines) >= 2:
                username = lines[0].strip()
                password = lines[1].strip()
    
    keyboard = xbmc.Keyboard(username, 'Enter Username')
    keyboard.doModal()
    if keyboard.isConfirmed():
        username = keyboard.getText()
    else:
        return
    
    keyboard = xbmc.Keyboard(password, 'Enter Password')
    keyboard.doModal()
    if keyboard.isConfirmed():
        password = keyboard.getText()
    else:
        return
    
    with open(LOGIN_FILE, "w") as file:
        file.write(username + "\n" + password)
    
    xbmcgui.Dialog().ok("Login Saved", "Your credentials have been saved.")

# Run the function to save login info
if __name__ == '__main__':
    save_login()
