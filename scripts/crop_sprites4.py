"""
从 ARPGbegin 工程的 Sprites/Ground/ 目录补两张地形图
"""
import os
from PIL import Image

SRC = r"C:\Users\lishen\Desktop\progra\new\ARPGbegin\Assets\Sprites\Ground"
DST = r"D:\1\mypro\daydaydream000.github.io\images\arpg"

def crop_grid(in_path, out_name, cols, rows, cell_w, cell_h, col, row):
    img = Image.open(in_path).convert("RGBA")
    x = col * cell_w
    y = row * cell_h
    cell = img.crop((x, y, x + cell_w, y + cell_h))
    bbox = cell.getbbox()
    if bbox:
        cell = cell.crop(bbox)
    out = os.path.join(DST, out_name)
    cell.save(out)
    print(f"-> {out_name} ({cell.size[0]}x{cell.size[1]})")

# Tilemap_Flat.png 640x256, 4x2 网格, 160x128
crop_grid(f"{SRC}\\Tilemap_Flat.png", "ground-tile.png", 4, 2, 160, 128, 0, 0)
# Tilemap_Elevation.png 256x512, 2x4 网格, 128x128
crop_grid(f"{SRC}\\Tilemap_Elevation.png", "mountain-tile.png", 2, 4, 128, 128, 0, 0)
# Shadows.png 192x192 单图
img = Image.open(f"{SRC}\\Shadows.png").convert("RGBA")
bbox = img.getbbox()
if bbox:
    img = img.crop(bbox)
img.save(os.path.join(DST, "shadow-tile.png"))
print(f"-> shadow-tile.png ({img.size[0]}x{img.size[1]})")
