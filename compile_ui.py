#!/usr/bin/python3

import os

PREFIX = "ui_"
OUTPUT_DIR = "modpack_downloader/ui"

for ui_name in os.listdir("ui"):
    py_name = PREFIX + os.path.splitext(ui_name)[0] + ".py"
    os.system(f"pyuic6 {os.path.join('ui', ui_name)} -o {os.path.join(OUTPUT_DIR, py_name)}")

