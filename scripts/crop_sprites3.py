"""
补两张：ground-tile 和 mountain-tile
"""
import os
from PIL import Image

SRC = r"C:\Users\lishen\Desktop\progra\new\ARPGbegin\Assets\Tiny Swords (Update 010)"
DST = r"D:\1\mypro\daydaydream000.github.io\images\arpg"

# Tilemap_Flat.png 在哪个目录？
import glob
for f in glob.glob(f"{SRC}\\**\\Tilemap_Flat.png", recursive=True):
    print(f"Found: {f}")
for f in glob.glob(f"{SRC}\\**\\Tilemap_Elevation.png", recursive=True):
    print(f"Found: {f}")
