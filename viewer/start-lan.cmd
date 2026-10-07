@echo off
cd /d "%~dp0.."
python viewer\server.py --lan --port 8765
