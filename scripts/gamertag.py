import xbmc
import xbmcgui
import xml.etree.ElementTree as ET
import re
import requests

# Path to the includes.xml file
XML_FILE_PATH = "Q:\\skin\\Cortana\\720p\\includes.xml"

class EditGamercardDialog:
    def __init__(self):
        self.load_defaults()

    def load_defaults(self):
        try:
            tree = ET.parse(XML_FILE_PATH)
            root = tree.getroot()
            self.rep_value = ""
            self.gamerscore_value = ""
            self.zone_value = ""
            for label in root.iter('label'):
                if label.text.startswith("Gamerscore: "):
                    self.gamerscore_value = label.text.split("Gamerscore: ")[1]
                elif label.text.startswith("Zone: "):
                    self.zone_value = label.text.split("Zone: ")[1]
            for texture in root.iter('texture'):
                match = re.search(r"rating/gamerscore(\d).png", texture.text)
                if match:
                    self.rep_value = match.group(1)
            xbmc.log("Loaded defaults - Rep: {}, Gamerscore: {}, Zone: {}".format(self.rep_value, self.gamerscore_value, self.zone_value), xbmc.LOGDEBUG)
        except Exception as e:
            xbmc.log("Error loading defaults: " + str(e), xbmc.LOGERROR)

    def open_keyboard(self, current_value, heading):
        keyboard = xbmc.Keyboard(current_value, heading)
        keyboard.doModal()
        if keyboard.isConfirmed():
            return keyboard.getText()
        return current_value

    def get_xbox_live_profile(self):
        try:
            gamertag = self.open_keyboard("", "Enter Xbox Live Gamertag")
            if not gamertag:
                return
            url = "https://playerdb.co/api/player/xbox/" + gamertag
            response = requests.get(url)
            data = response.json()
            if data["code"] == "player.found":
                gamerscore = data["data"]["player"]["meta"]["gamerscore"]
                reputation = data["data"]["player"]["meta"]["xboxOneRep"]
                rep_mapping = {
                    "GoodPlayer": "5",
                    "NeedsWork": "3",
                    "AvoidMe": "1"
                }
                rep_value = rep_mapping.get(reputation, "5")
                tree = ET.parse(XML_FILE_PATH)
                root = tree.getroot()
                for label in root.iter('label'):
                    if label.text.startswith("Gamerscore: "):
                        label.text = "Gamerscore: " + gamerscore
                for texture in root.iter('texture'):
                    if re.search(r"rating/gamerscore(\d).png", texture.text):
                        texture.text = "rating/gamerscore" + rep_value + ".png"
                tree.write(XML_FILE_PATH)
                xbmcgui.Dialog().ok("Success", "Xbox Live profile updated successfully!")
            else:
                xbmcgui.Dialog().ok("Error", "Failed to retrieve Xbox Live profile.")
        except Exception as e:
            xbmcgui.Dialog().ok("Error", "Failed to retrieve Xbox Live profile: " + str(e))

    def save_values(self, option):
        try:
            tree = ET.parse(XML_FILE_PATH)
            root = tree.getroot()
            if option == "Gamerscore":
                new_gamerscore_value = self.open_keyboard(self.gamerscore_value, "Enter Gamerscore")
                if new_gamerscore_value:
                    self.gamerscore_value = new_gamerscore_value
                    for label in root.iter('label'):
                        if label.text.startswith("Gamerscore: "):
                            label.text = "Gamerscore: " + new_gamerscore_value
            elif option == "Zone":
                new_zone_value = self.open_keyboard(self.zone_value, "Enter Zone")
                if new_zone_value:
                    self.zone_value = new_zone_value
                    for label in root.iter('label'):
                        if label.text.startswith("Zone: "):
                            label.text = "Zone: " + new_zone_value
            elif option == "Rep":
                new_rep_value = self.open_keyboard(self.rep_value, "Enter Rep (1-5)")
                if new_rep_value.isdigit() and 1 <= int(new_rep_value) <= 5:
                    self.rep_value = new_rep_value
                    for texture in root.iter('texture'):
                        if re.search(r"rating/gamerscore(\d).png", texture.text):
                            texture.text = "rating/gamerscore" + new_rep_value + ".png"
            tree.write(XML_FILE_PATH)
            xbmcgui.Dialog().ok("Success", "Changes saved successfully!")
        except Exception as e:
            xbmcgui.Dialog().ok("Error", "Failed to save changes: " + str(e))

    def show(self):
        options = ["Gamerscore", "Rep", "Zone", "Get Xbox Live Profile"]
        selected = xbmcgui.Dialog().select("CortanaID", options)
        if selected != -1:
            if options[selected] == "Get Xbox Live Profile":
                self.get_xbox_live_profile()
            else:
                self.save_values(options[selected])

if __name__ == "__main__":
    dialog = EditGamercardDialog()
    dialog.show()
