import os
import xbmc
import xbmcgui

D_DRIVE = "D:\\"  # Xbox disc drive

def launch_xbe():
    """Search for an .XBE file and launch it if found."""
    try:
        files = os.listdir(D_DRIVE)  # This will fail on audio CDs
        for file in files:
            if file.lower().endswith('.xbe'):
                xbe_path = os.path.join(D_DRIVE, file)
                xbmc.executebuiltin('RunXBE("%s")' % xbe_path)
                return True
    except:
        return False  # Ignore errors for now (likely an audio CD)
    return False

def play_dvd():
    """Play the disc using XBMC's PlayDVD function."""
    xbmc.executebuiltin("XBMC.PlayDVD")
    xbmc.sleep(1000)  # Wait briefly to allow playback to start
    xbmc.executebuiltin("XBMC.PlayerControl(FullScreen)")  # Switch to full-screen

def check_disc():
    """Main function to check the inserted disc and take appropriate action."""
    if os.path.exists(D_DRIVE):  # Check if the drive is accessible
        if launch_xbe():
            return
        play_dvd()  # If no XBE found, try playing the disc
    else:
        xbmcgui.Dialog().ok("Unrecognized Disc", "The disc is unreadable.", "1. Clean the disc with a soft cloth.", "2. Restart the console.")

if __name__ == "__main__":
    check_disc()
