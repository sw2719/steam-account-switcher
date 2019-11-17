# Steam Account Switcher
Steam Account Switching made easy (on Windows)

Written entirely in Python.

[Download in releases](https://github.com/sw2719/steam-account-switcher/releases)

[See this program in action](https://youtu.be/WFtv10RZ_UA)

STEAM is a trademark of Valve.

This app has no affiliation with Steam or Valve.

# Features
* Switch between your accounts with just few clicks.

* No more entering ID, password and Steam Guard code every time you login to another account.

* Unlike some other programs, your passwords are **NOT** required. Only uses your usernames.

* Auto-importing your Steam accounts. Do more clicking, less typing.

* Auto-updating is built-in. (Might be unavailable in certain updates.)

* No annoying update pop-up. You can just carry on and update later.

# How to use
1. Unpack the archive
2. Save it to some folder
3. Run the exe
**(Because this program alters your registry values AND is not code-signed, Windows SmartScreen or your Anti-virus might detect it as harmful software. You can just ignore it.)**

4. Import accounts from Steam or add them manually via Menu > Add accounts
* Your account names are saved in accounts.yaml located in the same folder where exe file is.
* There's no account limit, but window size increases as you add more account.

5. Click one of the buttons to change to desired account.
* If you previously set auto-login for that account, It just works.
* (It might show login prompt if you didn't login for a while. Steam doesn't let you auto-login after certain period of time. If this is the case, refer to below.)

* If you did not, Login prompt will appear when Steam launches. Make sure that the 'Remember my Password' is checked. Then enter your password and login as you normally would. You will need to enter your Steam Guard code if Mobile Authenticator is enabled. Next time you switch to that account, it will login automatically without entering Username / Password and Steam Guard code.

# Changelogs (for last 3 versions)
* Fixed a bug where app crashed if profile name contained unicode characters (v1.7)
* Changed how auto-updating works (v1.7)

* Implemented order changing (v1.6)
* Addded Settings UI (v1.6)
* Addded fallback for soft shutdown Steam mode (v1.6)
* Addded scrollbar to remove window (v1.6)
* Implemented mouse wheel-scrolling (v1.6)
* Fixed #7 (v1.6)
* Switched to YAML from Plain Text for accounts and config files (v1.6)
* Changed updater logic (v1.6)

* Changed first launch behaviour (v1.5)
* Bug fixes (v1.5)
* Added auto-updating (v1.5)
* Now your profile names are displayed (v1.5)
* Added settings functionality (v1.5)

# Upcoming Features / Improvements
* Auto launching app upon Steam restart (Not planned but coming)
* Setting custom name for accounts (Not planned but coming)
* Improving code & readability (Continuous)

# Source code information
* All other branches except master are considered as acitve-development branch and might have issues, bugs, WIP features, or might not just work at all.
* Written in Python 3.7
* Do not run updater.py in python interpreter. It's designed to run only in frozen environment.
* Requests, packaging, psutil, ruamel.yaml and gettext module are required.
* threading module needs to be installed if you are using Python version under 3.7.
* Source code is written in English. Translation to other languages is done with gettext.
* Keep in mind that I'm _quite_ new to Python. I'm sorry if my code is dirty, hard to read, or poorly written.

# Screenshots
![window](https://user-images.githubusercontent.com/22590718/63221824-87af7e00-c1d9-11e9-96e2-87508d2128b5.png)
![windowremove](https://user-images.githubusercontent.com/22590718/63221825-87af7e00-c1d9-11e9-8887-ed530c305166.png)
![windowadd](https://user-images.githubusercontent.com/22590718/63221826-88481480-c1d9-11e9-82eb-2b78dc9d528d.png)

# How it works
When you launch the program for the first time, the program fetches current auto-login user from registry and then adds it to accounts.txt.
When you add accounts, it saves your usernames to accounts.yaml.
(Steam saves your usernames in plain text as well. (It's VDF, but it's in plain text.)
When you press one of the 'account-changing' buttons, code below runs.

(modified)
```
reg_key = winreg.OpenKey(HKCU, r"Software\Valve\Steam", 0, winreg.KEY_ALL_ACCESS)
winreg.SetValueEx(reg_key, 'AutoLoginUser', 0, winreg.REG_SZ, *your_username*)
winreg.CloseKey(reg_key)
```
It changes the value of key 'AutoLoginUser' located at Steam registry path, tricking Steam to autologin with that username.
