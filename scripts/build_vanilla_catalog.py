import urllib.request
import json
import pathlib

def build():
    url = "https://raw.githubusercontent.com/PrismarineJS/minecraft-data/master/data/pc/1.21.1/items.json"
    req = urllib.request.Request(url, headers={"User-Agent": "CraftLab/1.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        raw = json.loads(response.read().decode("utf-8"))

    def classify(name: str) -> str:
        n = name.lower()
        if any(w in n for w in ["sword", "bow", "crossbow", "trident", "shield", "mace", "arrow", "wind_charge"]):
            return "combat"
        if any(w in n for w in ["pickaxe", "axe", "shovel", "hoe", "fishing_rod", "shears", "flint_and_steel", "spyglass", "brush", "compass", "clock", "lead", "name_tag"]):
            return "tools"
        if any(w in n for w in ["helmet", "chestplate", "leggings", "boots", "elytra", "horse_armor"]):
            return "armor"
        if any(w in n for w in ["apple", "bread", "porkchop", "beef", "chicken", "mutton", "rabbit", "cod", "salmon", "cookie", "melon", "carrot", "potato", "beetroot", "stew", "soup", "pie", "cake", "berries", "honey_bottle", "potion"]):
            return "food"
        if any(w in n for w in ["redstone", "repeater", "comparator", "target", "lever", "button", "pressure_plate", "piston", "observer", "hopper", "dispenser", "dropper", "daylight", "tripwire", "crafter", "sculk", "lightning_rod", "detector"]):
            return "redstone"
        if any(w in n for w in [
            "block", "stone", "ore", "planks", "log", "wood", "leaves", "dirt", "sand", "gravel", "brick", "glass",
            "concrete", "terracotta", "wool", "carpet", "slab", "stairs", "wall", "fence", "door", "trapdoor", "torch",
            "lantern", "chest", "furnace", "table", "bed", "box", "candle", "spawner", "vault", "coral", "sapling",
            "flower", "tuff", "copper", "deepslate", "granite", "diorite", "andesite", "obsidian", "ice", "snow",
            "sandstone", "prismarine", "purpur", "end_stone", "netherrack", "basalt", "blackstone"
        ]):
            return "blocks"
        return "items"

    processed = []
    for it in raw:
        name = it["name"]
        if name == "air":
            continue
        mat_id = name.upper()
        cat = classify(name)
        processed.append({
            "id": mat_id,
            "name": it.get("displayName", name.replace("_", " ").title()),
            "category": cat,
            "stack_size": it.get("stackSize", 64),
            "texture_url": f"https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.21.1/assets/minecraft/textures/item/{name}.png",
            "block_texture_url": f"https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.21.1/assets/minecraft/textures/block/{name}.png"
        })

    out_dir = pathlib.Path("CraftLab-backend/app/assets")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "vanilla_items_1.21.json"
    out_file.write_text(json.dumps(processed, indent=2), encoding="utf-8")
    print(f"Successfully generated {len(processed)} vanilla items in {out_file}")

if __name__ == "__main__":
    build()
