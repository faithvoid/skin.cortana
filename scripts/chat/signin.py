import os
import xbmc
import xbmcgui

# Define paths
SCRIPT_DIR = os.path.dirname(__file__)
PID_FILE = os.path.join(SCRIPT_DIR, "notifier.pid")
CHAT_SCRIPT = os.path.join(SCRIPT_DIR, "notifier.py")
LOGIN_FILE = xbmc.translatePath('special://home/userdata/profiles/{}/login.txt'.format(xbmc.getInfoLabel('System.ProfileName')))

# Function to delete the PID file and show notifications
def delete_pid():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        xbmc.executebuiltin('Notification(Cortana Chat, You have successfully logged out of Cortana Chat!, 5000)')
    else:
        xbmc.executebuiltin("RunScript(\"" + CHAT_SCRIPT + "\")")

# Function to prompt user for login details and save them
def prompt_login():
    dialog = xbmcgui.Dialog()
    if dialog.yesno("Cortana Chat", "No login file detected. Would you like to log in?"):
        keyboard = xbmc.Keyboard("", "Enter Username:")
        keyboard.doModal()
        if keyboard.isConfirmed():
            username = keyboard.getText()
        else:
            return
        
        keyboard = xbmc.Keyboard("", "Enter Password:", True)
        keyboard.doModal()
        if keyboard.isConfirmed():
            password = keyboard.getText()
        else:
            return
        
        with open(LOGIN_FILE, "w") as f:
            f.write(username + "\n")
            f.write(password + "\n")
        
        xbmc.executebuiltin('Notification(Cortana Chat, Login details saved successfully!, 5000)')

# Main execution logic
if __name__ == '__main__':
    if not os.path.exists(LOGIN_FILE):
        prompt_login()
    
    if not os.path.exists(PID_FILE):
        # If notifier.pid does not exist, immediately launch chat.py
        xbmc.executebuiltin("RunScript(\"" + CHAT_SCRIPT + "\")")
        xbmc.executebuiltin('Notification(Cortana Chat, You have successfully logged into Cortana Chat!, 5000)')
    else:
        # Otherwise, try deleting the PID file
        delete_pid()
