# Steam Account Switcher
Steam Account Switching made easy (on Windows)

Written in Python

[Download in releases](https://github.com/sw2719/steam-account-switcher/releases)

[See this program in action](https://youtu.be/WFtv10RZ_UA)

STEAM is a trademark of Valve.

This app has no affiliation with Steam and Valve.

# Features
* Switch between your accounts with just few clicks.

* No more entering ID, password and Steam Guard code every time you login to another account.

* Unlike some other programs, your passwords are **NOT** required. Only uses your usernames.

* Auto-importing your Steam accounts. Do more clicking, less typing.

* Auto-updating is built-in.

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
* Added server message displaying functionality. (v1.7.2)
* Added update download progress bar. (v1.7.1)
* Fixed crash that occured if unicode characters existed in profile name. (v1.7)
* Changed update UI. (v1.7)
* Updated auto updating implementation. (v1.7)
* Changed how profile name is displayed. (v1.7)
* Added a setting to choose whether app exits after restarting Steam or not. (v1.7)

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
