import xbmc
import xbmcgui
import xml.etree.ElementTree as ET

# Path to the includes.xml file
XML_FILE_PATH = "Q:\\path\\to\\includes.xml"

class EditGamercardDialog:
    def __init__(self):
        self.load_defaults()

    def load_defaults(self):
        # Load current values from the XML file
        try:
            tree = ET.parse(XML_FILE_PATH)
            root = tree.getroot()

            # Initialize default values
            self.rep_value = ""
            self.gamerscore_value = ""
            self.zone_value = ""

            # Iterate through all the label elements to find the relevant values
            for label in root.iter('label'):
                if label.text.startswith("Rep: "):
                    self.rep_value = label.text.split("Rep: ")[1]
                elif label.text.startswith("Gamerscore: "):
                    self.gamerscore_value = label.text.split("Gamerscore: ")[1]
                elif label.text.startswith("Zone: "):
                    self.zone_value = label.text.split("Zone: ")[1]

            # Log the initial values for debugging
            xbmc.log(f"Loaded defaults - Rep: {self.rep_value}, Gamerscore: {self.gamerscore_value}, Zone: {self.zone_value}", xbmc.LOGDEBUG)

        except Exception as e:
            xbmc.log("Error loading defaults: " + str(e), xbmc.LOGERROR)

    def open_keyboard(self, current_value, heading):
        # Use the xbmc keyboard for user input
        keyboard = xbmc.Keyboard(current_value, heading)
        keyboard.doModal()

        if keyboard.isConfirmed():
            return keyboard.getText()
        return current_value

    def save_values(self):
        try:
            # Load the XML and update the fields
            tree = ET.parse(XML_FILE_PATH)
            root = tree.getroot()

            # Iterate through all the label elements to find the relevant ones and update them
            for label in root.iter('label'):
                if label.text.startswith("Rep: "):
                    label.text = "Rep: " + self.open_keyboard(self.rep_value, "Enter Rep")
                elif label.text.startswith("Gamerscore: "):
                    label.text = "Gamerscore: " + self.open_keyboard(self.gamerscore_value, "Enter Gamerscore")
                elif label.text.startswith("Zone: "):
                    label.text = "Zone: " + self.open_keyboard(self.zone_value, "Enter Zone")

            # Save changes back to the XML file
            tree.write(XML_FILE_PATH)
            xbmcgui.Dialog().ok("Success", "Changes saved successfully!")

        except Exception as e:
            xbmcgui.Dialog().ok("Error", "Failed to save changes: " + str(e))

    def show(self):
        # Ask for confirmation to save
        result = xbmcgui.Dialog().yesno("Edit Gamer Card", "Would you like to edit your gamertag details?", "", "", "Yes", "No")
        if result == 1:
            self.save_values()

# Main execution
if __name__ == "__main__":
    dialog = EditGamercardDialog()
    dialog.show()
