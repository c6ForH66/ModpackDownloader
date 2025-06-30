# ModpackDownloader
Minecraft Modpack Downloader

### **Download from [GitHub releases page](https://github.com/c6ForH66/ModpackDownloader/releases)**

## Features
- Support Curseforge modpacks and FTB modpacks
- No "blocked mods" problem like in PrismLauncher, you can get rid of the annoying Overwolf app
- Ultrafast download by using aria2 (download alomst any modpack in a minute with a 1Gbps connection)

## Installation
### Windows
- Download from releases page and extract the archive (including `aria2c.exe` and `aria2.conf`)
- Launch the program

### Linux (or if you want to run from source code)
- Install Python 3 (at least 3.11)
- Install requirements in `requirements.txt`
- Run `./gen_api_key.sh` if you don't have a curseforge api key. Otherwise follow instructions in `api_key.py.example`
- Run `./main.py`

## Usage
- Click `File -> Download a modpack` and follow the instructions
- For FTB packs, you have to enter pack id and version id. To get these values, go to FTB website, choose your modpack and scroll down until you find something like this:

  ![image](https://github.com/user-attachments/assets/ab26d394-9323-44f9-8602-2123ec66d6f0)

- When the download finishes, a dialog will pop up showing the mc version, modloader version and minecraft dir. Create a new instance in your launcher and copy everything in the `minecraft_dir` into the game directory

## TODO
- Better UI
- Support Modrinth modpacks
- Directly import to launchers like PrismLauncher
- Export as MultiMC-compatible zip file
