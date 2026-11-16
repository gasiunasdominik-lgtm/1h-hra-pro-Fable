#!/bin/bash
# Hra mimo obrazovku vyfoti pohledy do Saved/Shots/view_N.png a sama skonci. $1 = sekundy zahrivani (shadery).
cd /mnt/c/Users/dominik/documents/Hry/1h-hra-pro-Fable
rm -f Saved/Shots/view_*.png
timeout 600 Tools/go.sh play -shots -shotwarm=${1:-25} -RenderOffscreen -nosound -unattended > /dev/null 2>&1
ls Saved/Shots
