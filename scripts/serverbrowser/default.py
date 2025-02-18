import xbmc
import xbmcgui
import os

# Define script paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the script's directory
INSIGNIA = os.path.join(SCRIPT_DIR, "insignia.py")
XLINKKAI = os.path.join(SCRIPT_DIR, "xlinkkai.py")

# Show a dialog with two options
dialog = xbmcgui.Dialog()
choice = dialog.select("Select an option", ["Insignia", "XLink Kai"])

# Execute the selected script
if choice == 0:
    xbmc.executebuiltin('RunScript("{}")'.format(INSIGNIA))
elif choice == 1:
    xbmc.executebuiltin('RunScript("{}")'.format(XLINKKAI))
