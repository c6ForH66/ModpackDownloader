# ModpackDownloader
Minecraft Modpack Downloader
## Features
- Support for curseforge modpacks and ftb modpacks
- No "blocked mods" problem, fully automatical
- Ultrafast download by aria2 (download alomst any modpack in a minute with a 1Gbps connection)
- A real usable UI, no console commands

## Installation
### Windows
- Download from releases page and extract the archive (including `aria2c.exe` and `aria2.conf`)
- You may need to add the program to the exclusion list of your antivirus software and the binary is safe. (very common `Trojan:Win32/Wacatac.B!ml` false positive)
- If you still don't trust the binary, read below

### Linux (or if you want to run from source code)
- Install Python 3 (at least 3.11)
- Install requirements in `requirements.txt`
- Run `./gen_api_key.sh` if you don't have a curseforge api key. Otherwise follow instructions in `api_key.py.example`
- Run `./main.py`

## Usage
- Click `File -> Download a modpack` and follow the instructions
- For FTB packs, you have to enter pack id and version id. To get these values, go to FTB website, choose your modpack and scroll down until you find something like this:

  ![image](https://github.com/user-attachments/assets/ab26d394-9323-44f9-8602-2123ec66d6f0)

- When the download finishes, a dialog will pop up and shows the mc version, modloader version and minecraft dir. Create a new instance in your launcher and copy everything in the `minecraft_dir` into the game directory

## TODO
- Better UI
- Export as multimc-compatible format so you can install it with only one drag!
