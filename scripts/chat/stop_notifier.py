# Cortana Chat v2.0 by faithvoid - https://github.com/faithvoid/script.cortanachatv2

import os
import xbmc
import xbmcgui

# Define the path to the PID file
PID_FILE = os.path.join(os.path.dirname(__file__), "notifier.pid")

# Function to delete the PID file and show dialog notifications
def delete_pid():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
        xbmcgui.Dialog().ok("Cortana Chat", "You have successfully logged out of Cortana Chat!")
    else:
        xbmcgui.Dialog().ok("Cortana Chat", "Logout failed! The notifier might not be running.")

# Run the function to delete the PID file
if __name__ == '__main__':
    delete_pid()
