# An alternative to the Twitch/Curse launcher for MultiMC

Requirements:
* Python 3.6.2
* BeautifulSoup 4.6.0
* Requests 2.18.3

(Other versions may work, but those are the tested ones)

---

# Installing Requirements

## Linux

### Arch Linux

```
sudo pacman -S python python-beautifulsoup4 python-requests
```

### Other

If you know how to install the dependencies on another distro, please open a pull request or an issue

## MacOS

If you know how to install the dependencies on MacOS, please open a pull request or an issue

## Windows

If you know how to install the dependencies on Windows, please open a pull request or an issue

---

# Using

## Install

### Linux

```
git clone https://github.com/joonatoona/OpenMineMods.git
cd OpenMineMods
```

(I will make a pip package at some point)

### MacOS

Same as Linux

### Windows

Download https://github.com/joonatoona/OpenMineMods/archive/master.zip and unzip it  
Then in the unzipped folder, right click and select `Open in CMD` (Or something like that, let me know if it's different)

## Test

```
python3 tests.py
```

If not every test passed, please open an issue with `results.json` and your MultiMC installation folder.

## Install Modpack

```
python3 ModpackDownloader.py
```

It might ask for your MultiMC installation folder, if it can't automatically find it.  
If it does ask for the folder, please open an issue with your MultiMC installation folder.

## Add Mods

```
python3 AddMod.py
```

It might ask for your MultiMC installation folder, if it can't automatically find it.
If it does ask for the folder, please open an issue with your MultiMC installation folder.

