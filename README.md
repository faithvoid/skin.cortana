# Cortana - A modern, sleek "Xbox 180" style theme for XBMC4Xbox, with an emphasis on social / multiplayer feature integration.
## Requires [Cortana Server Browser](https://github.com/faithvoid/script.cortanaserverbrowser), [Cortana Chat](https://github.com/faithvoid/script.cortanachatv2), [Cortana Wireless (optional)](https://github.com/faithvoid/script.cortanawireless) & [xSky](https://github.com/faithvoid/plugin.programs.xSky) to function correctly!

## Features:
- Replaced the broken Weather page with Cortana, a series of scripts that allows you to view & join active Insignia/XLink Kai sessions, events, view server statistics, get new match notifications, get Cortana/Insignia/XLink Kai news, check your Insignia DNS settings, send/receive messages, and more!

- Get social on your Xbox again! Using Cortana Chat, you can use the AT protocol (aka Bluesky) to chat with fellow gamers, invite them to games, set beacons to find other players, and more!

- Show off your gamerscore and reputation with CortanaID, a reimplementation of gamertags from MC360! Set it manually, or pull it from your Xbox Live profile!

- Paired with Cortana Wireless, you can easily connect a Raspberry Pi or similar SBC as a wireless network card for your Xbox and easily manage your Wi-Fi settings!

- Per-profile save games and social features! Share your Xbox with friends and family? Everyone gets their own accounts and saves!

- "Guide button" feature that reimplements most of the features you know and love from the 360, using Cortana Chat! Just click in the right stick and you have full access to social features, settings, and more!

- Toast notifications for messages and notifications via Cortana Chat, and toast notifications for current XLink Kai / Insignia sessions via Cortana Server Browser!
  
- Added quality-of-life functions to the Applications page (Renamed certain items to seem more "official", added "Addons" & "Scripts" buttons, "Dashboard" button, "Xbox Live" (Network Settings) button, and "Detach Virtual Disk").
  
- Added quality-of-life functions to the Media page (added Video/Music/Photo add-ons!), as well as watched media indicators that were missing from the original JX 720!

- Use Cortana Marketplace to quickly download homebrew games & emulators! If stored in a .zip/.rar file, Cortana Marketplace will automatically extract the homebrew to your Homebrew folder so you can instantly hop into the action!
  
- Neon wallpapers have been swapped out for pastel abstract shapes (based off of old macOS 9 wallpapers), making the UI easier on the eyes.

- Multiple open-source font options for accessibility!
  
- Reintroduced Gamertag function from MC360! (Name & Avatar are automatically pulled from current XBMC profile, and you can manually edit your Rep, Gamerscore & Zone in Cortana Settings in the Guide menu!) 
  
- Need to fix something? Cortana Settings Menu has you covered! With shortcuts to the Dashboard, Internet Connection Test utilities, Notification Settings, Clear Cache, XBMC4Gamers Scripts, Updates, and more, Cortana can help you out of most pickles!

- ## Menu Screenshots:
![cortana1](screenshots/1.png)
![cortana2](screenshots/2.png)
![cortana3](screenshots/3.png)
![cortana4](screenshots/4.png)
![cortana5](screenshots/5.png)
![cortana6](screenshots/6.png)
![cortana7](screenshots/7.png)

## Cortana Server Browser:
![Cortana Server Browser - 1](screenshots/csb1.png)
![Cortana Server Browser - 2](screenshots/csb2.png)
![Cortana Server Browser - 3](screenshots/csb3.png)

## Cortana Chat
![Cortana Chat - 1](screenshots/cc1.png)
![Cortana Chat - 2](screenshots/cc2.png)
![Cortana Chat - 3](screenshots/cc3.png)
![Cortana Chat - 4](screenshots/cc4.png)

## Themes
### Aero (WIP)
![Aero](screenshots/aero-test.png)
### Aero Lite (WIP)
![Aero Lite](screenshots/aerolite-test.png)

## TODO:
- Further work on "Cortana Marketplace" (need to find a futureproof source for Xbox homebrew and possibly convert it from a script into an add-on for image previews)
- Fix wallpaper memory usage bug.
- Fix up & release Cortana Server Browser & Cortana Chat.
- Fix multi-user savegame script.
- Make black backgrounds semi-transparent for a more mid-2000s aesthetic.
- Work on "Aero" and "Aero Lite" themes (Aero Lite requires the most work, as the font colour system needs to be re-done to render fonts and their shadows correctly).

## How to install:
- Download latest release from the Releases category
- Copy "Cortana" to "Q:\skins\"
- Change your skin to Cortana in the XBMC Appearance menu.
- ???
- Profit!

## Bugs:
- Cortana blade is currently a bit visually glitchy and visibly says "Refresh" when switching pages. It's a "blink and you'll mix it" issue but it's still present.
- Signing in to Cortana Chat can currently hang the system when launching a game right as the script refreshes. Looking into a fix for this ASAP before release.
- You tell me.

## Credits:
- Steve Matteson - Open Sans font
- Jezz_X & Team Blackbolt - JX720 & MC360, respectively (this project uses JX720 as a base, with MC360 assets reincorporated where possible)
