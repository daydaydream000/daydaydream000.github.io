"""
从 Tiny Swords spritesheet 裁剪出单帧图片，存到 images/arpg/
"""
import os
from PIL import Image

SRC = r"C:\Users\lishen\Desktop\progra\new\ARPGbegin\Assets\Tiny Swords (Update 010)"
DST = r"D:\1\mypro\daydaydream000.github.io\images\arpg"
os.makedirs(DST, exist_ok=True)

def crop_grid(in_path, out_name, cols, rows, cell_w, cell_h, target_col, target_row):
    """从 spritesheet 裁出指定 (row, col) 那一格。row 0 是最上面。"""
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
    """直接复制并裁掉透明边。"""
    img = Image.open(in_path).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    out = os.path.join(DST, out_name)
    img.save(out)
    print(f"  -> {out_name} ({img.size[0]}x{img.size[1]})")

# === 角色 ===
# 1. Warrior (1152x1536, 6x8, 192x192)
crop_grid(f"{SRC}\\Factions\\Knights\\Troops\\Warrior\\Blue\\Warrior_Blue.png",
          "warrior-idle.png", 6, 8, 192, 192, 0, 0)
crop_grid(f"{SRC}\\Factions\\Knights\\Troops\\Warrior\\Blue\\Warrior_Blue.png",
          "warrior-walk.png", 6, 8, 192, 192, 0, 2)

# 2. Torch Red (1344x960, 6x4, 224x240)
crop_grid(f"{SRC}\\Factions\\Goblins\\Troops\\Torch\\Red\\Torch_Red.png",
          "torch-red-idle.png", 6, 4, 224, 240, 0, 0)
crop_grid(f"{SRC}\\Factions\\Goblins\\Troops\\Torch\\Red\\Torch_Red.png",
          "torch-red-walk.png", 6, 4, 224, 240, 0, 2)

# 3. Archer
crop_grid(f"{SRC}\\Factions\\Knights\\Troops\\Archer\\Blue\\Archer_Blue.png",
          "archer-idle.png", 6, 8, 192, 192, 0, 0)

# === 地形 ===
# 4. Bridge_All - 先看一下尺寸
import subprocess
# 跳过 - 直接用 Bridge 文件夹的图
crop_image(f"{SRC}\\Terrain\\Bridge\\Bridge_All.png", "bridge.png")

# 5. Water
crop_image(f"{SRC}\\Terrain\\Water\\Water.png", "water.png")

# 6. Rocks
crop_image(f"{SRC}\\Terrain\\Water\\Rocks\\Rocks_01.png", "rock.png")

# 7. Foam - 看尺寸再决定网格
img = Image.open(f"{SRC}\\Terrain\\Water\\Foam\\Foam.png")
print(f"Foam size: {img.size}")

# === 建筑 ===
# 8. Castle
crop_image(f"{SRC}\\Factions\\Knights\\Buildings\\Castle\\Castle_Blue.png", "castle.png")

# 9. House Blue
crop_image(f"{SRC}\\Factions\\Knights\\Buildings\\House\\House_Blue.png", "house-blue.png")

# 10. Tower Blue
crop_image(f"{SRC}\\Factions\\Knights\\Buildings\\Tower\\Tower_Blue.png", "tower.png")

# 11. Goblin House
crop_image(f"{SRC}\\Factions\\Goblins\\Buildings\\Wood_House\\Goblin_House.png", "goblin-house.png")

# 12. Wood Tower
crop_image(f"{SRC}\\Factions\\Goblins\\Buildings\\Wood_Tower\\Wood_Tower_Red.png", "wood-tower.png")

# === 资源 ===
# 13. Tree - 4x2
crop_grid(f"{SRC}\\Resources\\Trees\\Tree.png",
          "tree.png", 4, 2, 192, 192, 0, 0)

# 14. Gold Mine
crop_image(f"{SRC}\\Resources\\Gold Mine\\GoldMine_Active.png", "goldmine.png")

# 15. Sheep
crop_image(f"{SRC}\\Resources\\Sheep\\HappySheep_Idle.png", "sheep.png")

# 16. Dead
crop_image(f"{SRC}\\Factions\\Knights\\Troops\\Dead\\Dead.png", "dead.png")

# === 装饰 ===
crop_image(f"{SRC}\\Deco\\01.png", "deco-01.png")
crop_image(f"{SRC}\\Deco\\02.png", "deco-02.png")
crop_image(f"{SRC}\\Deco\\05.png", "deco-05.png")
crop_image(f"{SRC}\\Deco\\08.png", "deco-08.png")

print(f"\n总共生成 {len(os.listdir(DST))} 张单帧图")
