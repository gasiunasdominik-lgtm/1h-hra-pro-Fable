#!/bin/bash
# Pouziti z WSL: Tools/go.sh build|level|bake|play [dalsi argumenty]
cd /mnt/c/Users/dominik/documents/Hry/1h-hra-pro-Fable
s=$1; shift
cmd.exe /c "Tools\\win\\$s.bat" "$@"
