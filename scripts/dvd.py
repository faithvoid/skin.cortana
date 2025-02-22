import os
import xbmc
import xbmcgui

D_DRIVE = "D:\\"  # Xbox disc drive

def launch_xbe():
    """Search for an .XBE file and launch it if found."""
    try:
        files = os.listdir(D_DRIVE)  # This will fail on audio CDs
        for file in files:
            if file.endswith('default.xbe'):
                xbe_path = os.path.join(D_DRIVE, file)
                xbmc.executebuiltin('RunXBE("%s")' % xbe_path)
                return True
    except:
        return False  # Ignore errors for now (likely an audio CD)
    return False

def play_dvd():
    """Play the disc using XBMC's PlayDVD function."""
    xbmc.executebuiltin("XBMC.PlayDVD")

def check_disc():
    """Main function to check the inserted disc and take appropriate action."""
    if xbmc.getCondVisibility("System.HasMediaDVD"):  # Check if a readable disc is inserted
        if launch_xbe():
            return
        play_dvd()  # If no XBE found, try playing the disc
    else:
        xbmcgui.Dialog().ok("Unrecognized Disc", "The disc is missing or unreadable.", "1. Clean the disc with a soft cloth and / or reinsert it.", "2. Restart the console.")

if __name__ == "__main__":
    check_disc()
