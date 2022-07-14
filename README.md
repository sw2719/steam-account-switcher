<img align="right" src="https://user-images.githubusercontent.com/22590718/111099604-3750fb80-8589-11eb-90be-bfbef898acdf.PNG">

# Steam Account Switcher
Lightweight, fast account switcher for Steam.

Written in Python

[이 문서는 한국어로도 읽을 수 있습니다.](https://github.com/sw2719/steam-account-switcher/blob/master/README_ko.md)

[Download in releases](https://github.com/sw2719/steam-account-switcher/releases)

STEAM is a trademark of Valve Corporation.

This app has no affiliation with Steam and Valve.

# Features
* Switch between your accounts with just few clicks.

* No more entering ID, password and Steam Guard code every time you login to another account.

* Restarting Steam with single click.

* Unlike some other programs, your passwords are **NOT** required. Only uses your usernames.

* Auto-importing your Steam accounts. Do more clicking, less typing.

* Auto-updating is built-in, and it's fast. (Unless GitHub's server is having a hard time..)

# Requirements (for executable release)
* Windows 8.1 or newer
  - 64-bit is no longer required since version 2.7.
* Steam installed correctly
* Visual C++ Redistributable for Visual Studio 2015 or 2017
  - Chances are it's already installed, but if it isn't, you can download it below.
  - [Download for 32-bit](https://aka.ms/vs/16/release/vc_redist.x32.exe)
  - [Download for 64-bit](https://aka.ms/vs/16/release/vc_redist.x64.exe)

# How to use
1. Unpack the archive to desired folder
2. Run the exe (Do NOT change the name of the executable!)
* Because this program is not code-signed, Windows SmartScreen might pop up. Click 'More info' and then 'Run anyway'.
 
3. Import accounts from Steam or add them manually via Menu > Add accounts
* Your account names are saved in accounts.yml located in the same folder where exe file is.

4. Click one of the buttons to change to desired account.
* Steam login prompt might appear if you are using this program for the first time. Just check 'Remember password' and login. It will work next time. 
  - You need to do this for every account except the one you have been using as autologin account prior to using this program.
  - **If you ever add more accounts, you have to do this for them as well. And if you don't login to certain account for a while, you will have to do this again for that account due to Steam revoking autologin access.**

# FAQ
* Login prompt appears! Fake program!
  - See How to use-4. Right above.

* Windows SmartScreen says this program is potentially harmful!
  - That's because I didn't sign my executable with EV certificate which costs money. As you know, this program is free. Also, it's malicious code-free, so don't worry about it.

* I have a request! / I found a bug!
  - Bug reports and requests are always welcome. Please submit an issue.

* Some of the elements in settings are missing!
  - Delete config.yml and launch application again.

# Source code information
* All other branches except master are considered as acitve-development branch and might have issues, bugs, WIP features, or might not just work at all.
* At least Python 3.7 is required.
* Do not run updater.py in python interpreter. It's designed to run only in frozen environment.
* Use requirements.txt to install dependencies.
* Source code is written in English. Translation to other languages is done with gettext.
