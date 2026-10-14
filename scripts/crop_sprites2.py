"""
修正版：把所有 spritesheet 正确切成单帧
"""
import os
from PIL import Image

SRC = r"C:\Users\lishen\Desktop\progra\new\ARPGbegin\Assets\Tiny Swords (Update 010)"
DST = r"D:\1\mypro\daydaydream000.github.io\images\arpg"
os.makedirs(DST, exist_ok=True)

def crop_grid(in_path, out_name, cols, rows, cell_w, cell_h, target_col, target_row):
    img = Image.open(in_path).convert("RGBA")
    x = target_col * cell_w
    y = target_row * cell_h
    cell = img.crop((x, y, x + cell_w, y + cell_h))
    bbox = cell.getbbox()
    if bbox:
        cell = cell.crop(bbox)
    out = os.path.join(DST, out_name)
    cell.save(out)
    print(f"  -> {out_name} ({cell.size[0]}x{cell.size[1]})")

def crop_image(in_path, out_name):
    img = Image.open(in_path).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    out = os.path.join(DST, out_name)
    img.save(out)
    print(f"  -> {out_name} ({img.size[0]}x{img.size[1]})")

# === 横长条 spritesheet 修正 ===
# Rocks: 1024x128, 8 帧 × 128 宽
# 但 Rock 实际是 8x1 网格，bbox 太窄了，用一张大的
img = Image.open(f"{SRC}\\Terrain\\Water\\Rocks\\Rocks_01.png").convert("RGBA")
# 直接看第 1 帧
cell = img.crop((0, 0, 128, 128))
# 找最大 bbox - 实际岩石都是淡蓝色，背景可能透明
bbox = cell.getbbox()
print(f"  Rock[0,0] bbox: {bbox}, full size: {cell.size}")
cell.save(os.path.join(DST, "rock.png"))

# Sheep: 1024x128, 8 帧 × 128 宽
crop_grid(f"{SRC}\\Resources\\Sheep\\HappySheep_Idle.png",
          "sheep.png", 8, 1, 128, 128, 0, 0)

# Wood Tower: 896x155 - 看实际尺寸
img = Image.open(f"{SRC}\\Factions\\Goblins\\Buildings\\Wood_Tower\\Wood_Tower_Red.png")
print(f"Wood Tower size: {img.size}")
# 896/5 ≈ 179, 155 高度. 实际是 5x1, 179x155
crop_grid(f"{SRC}\\Factions\\Goblins\\Buildings\\Wood_Tower\\Wood_Tower_Red.png",
          "wood-tower.png", 5, 1, 179, 155, 0, 0)

# Dead: 896x256, 7x2 网格（死亡动画逐帧）
crop_grid(f"{SRC}\\Factions\\Knights\\Troops\\Dead\\Dead.png",
          "dead.png", 7, 2, 128, 128, 6, 1)
# 骷髅头（中间帧）
crop_grid(f"{SRC}\\Factions\\Knights\\Troops\\Dead\\Dead.png",
          "skull.png", 7, 2, 128, 128, 3, 0)
