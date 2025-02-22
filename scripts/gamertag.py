import xbmc
import xbmcgui
import xml.etree.ElementTree as ET
import re

# Path to the includes.xml file
XML_FILE_PATH = "Q:\\skin\\Cortana\\720p\\includes.xml"

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
                if label.text.startswith("Gamerscore: "):
                    self.gamerscore_value = label.text.split("Gamerscore: ")[1]
                elif label.text.startswith("Zone: "):
                    self.zone_value = label.text.split("Zone: ")[1]

            # Iterate through all the texture elements to find the relevant rep value
            for texture in root.iter('texture'):
                match = re.search(r"rating/gamerscore(\d).png", texture.text)
                if match:
                    self.rep_value = match.group(1)

            # Log the initial values for debugging
            xbmc.log("Loaded defaults - Rep: {}, Gamerscore: {}, Zone: {}".format(self.rep_value, self.gamerscore_value, self.zone_value), xbmc.LOGDEBUG)

        except Exception as e:
            xbmc.log("Error loading defaults: " + str(e), xbmc.LOGERROR)

    def open_keyboard(self, current_value, heading):
        # Use the xbmc keyboard for user input
        keyboard = xbmc.Keyboard(current_value, heading)
        keyboard.doModal()

        if keyboard.isConfirmed():
            return keyboard.getText()
        return current_value

    def save_values(self, option):
        try:
            # Load the XML and update the fields
            tree = ET.parse(XML_FILE_PATH)
            root = tree.getroot()

            if option == "Gamerscore":
                for label in root.iter('label'):
                    if label.text.startswith("Gamerscore: "):
                        label.text = "Gamerscore: " + self.open_keyboard(self.gamerscore_value, "Enter Gamerscore")
            elif option == "Zone":
                for label in root.iter('label'):
                    if label.text.startswith("Zone: "):
                        label.text = "Zone: " + self.open_keyboard(self.zone_value, "Enter Zone")
            elif option == "Rep":
                new_rep_value = self.open_keyboard(self.rep_value, "Enter Rep (1-5)")
                if new_rep_value.isdigit() and 1 <= int(new_rep_value) <= 5:
                    for texture in root.iter('texture'):
                        if re.search(r"rating/gamerscore(\d).png", texture.text):
                            texture.text = "rating/gamerscore{}.png".format(new_rep_value)

            # Save changes back to the XML file
            tree.write(XML_FILE_PATH)
            xbmcgui.Dialog().ok("Success", "Changes saved successfully!")

        except Exception as e:
            xbmcgui.Dialog().ok("Error", "Failed to save changes: " + str(e))

    def show(self):
        # Display a menu with options
        options = ["Edit Gamerscore", "Edit Rep", "Edit Zone"]
        selected = xbmcgui.Dialog().select("Select Option", options)
        if selected != -1:
            self.save_values(options[selected])

# Main execution
if __name__ == "__main__":
    dialog = EditGamercardDialog()
    dialog.show()
