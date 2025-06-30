#!/bin/bash
# Generate a curseforge api key using magic

mkdir .tmp
cd .tmp
wget -O curseforge.zip https://curseforge.overwolf.com/downloads/curseforge-latest-linux.zip
unzip curseforge.zip
7z e -y ./*.AppImage resources/app.asar.unpacked/plugins/curse/linux/Curse.Agent.Host
KEY=$(strings -e l ./Curse.Agent.Host | grep -F '$2a$10$')
cd ..
rm .tmp/* -rf
rmdir .tmp/

echo "CF_API_KEY='${KEY}'" > api_key.py
echo API key generated
