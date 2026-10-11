import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple

PUA_MIN = 0xE000
PUA_MAX = 0xF8FF
HEX_REGEX = re.compile(r"^[0-9A-Fa-f]{4}$")


def normalize_hex(hex_code: str) -> str:
    cleaned = hex_code.strip().replace("\\u", "").replace("U+", "").upper()
    return cleaned


def is_valid_pua_code(codepoint_int: int) -> bool:
    return PUA_MIN <= codepoint_int <= PUA_MAX


def get_font_file_path(workspace_dir: Path, namespace: str = "craftlab", font_name: str = "default") -> Path:
    return workspace_dir / "assets" / namespace / "font" / f"{font_name}.json"


def scan_registered_glyphs(workspace_dir: Path, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Scans font provider definitions in the workspace to catalog all registered glyphs.
    Returns a list of structured glyph entries with unicode character, hex code, height, and file path.
    """
    glyphs: List[Dict[str, Any]] = []
    assets_dir = workspace_dir / "assets"
    if not assets_dir.exists():
        return glyphs

    namespaces = [assets_dir / namespace] if namespace else [d for d in assets_dir.iterdir() if d.is_dir()]

    for ns_dir in namespaces:
        ns_name = ns_dir.name
        font_dir = ns_dir / "font"
        if not font_dir.exists():
            continue

        for font_file in font_dir.glob("*.json"):
            try:
                data = json.loads(font_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            providers = data.get("providers", [])
            for p in providers:
                if p.get("type") != "bitmap":
                    continue

                chars = p.get("chars", [])
                file_ref = p.get("file", "")
                height = p.get("height", 8)
                ascent = p.get("ascent", 7)

                # Derive identifier from filename
                raw_filename = file_ref.split("/")[-1] if "/" in file_ref else file_ref
                glyph_id = raw_filename.replace(".png", "") if raw_filename else "glyph"

                for row_idx, row in enumerate(chars):
                    for col_idx, char_str in enumerate(row):
                        if not char_str or char_str == "\u0000":
                            continue
                        code_point = ord(char_str)
                        hex_str = f"{code_point:04X}"

                        glyphs.append({
                            "id": glyph_id if len(chars) == 1 and len(row) == 1 else f"{glyph_id}_{row_idx}_{col_idx}",
                            "character": char_str,
                            "hex": hex_str,
                            "file": file_ref,
                            "height": height,
                            "ascent": ascent,
                            "namespace": ns_name,
                            "font_file": font_file.name,
                            "is_pua": is_valid_pua_code(code_point)
                        })

    return glyphs


def get_allocated_pua_hexes(workspace_dir: Path, namespace: Optional[str] = None) -> Set[str]:
    glyphs = scan_registered_glyphs(workspace_dir, namespace)
    return {g["hex"] for g in glyphs if g["is_pua"]}


def allocate_next_pua(used_hexes: Set[str], start_hex: str = "E001") -> str:
    start_int = int(normalize_hex(start_hex), 16)
    if start_int < PUA_MIN:
        start_int = PUA_MIN

    for cp in range(start_int, PUA_MAX + 1):
        hex_cand = f"{cp:04X}"
        if hex_cand not in used_hexes:
            return hex_cand

    # Wrap around if starting above PUA_MIN
    for cp in range(PUA_MIN, start_int):
        hex_cand = f"{cp:04X}"
        if hex_cand not in used_hexes:
            return hex_cand

    raise ValueError("PUA codepoint exhaustion: all Private Use Area slots (E000-F8FF) are occupied.")


def validate_pua_hex(hex_code: str, used_hexes: Set[str], current_glyph_hex: Optional[str] = None) -> Tuple[bool, str]:
    normalized = normalize_hex(hex_code)
    if not HEX_REGEX.match(normalized):
        return False, "Invalid hexadecimal format: must be 4 hex digits (e.g. E001)"

    codepoint = int(normalized, 16)
    if not is_valid_pua_code(codepoint):
        return False, f"Codepoint \\u{normalized} outside Minecraft PUA range (E000-F8FF)"

    if normalized in used_hexes and normalized != (normalize_hex(current_glyph_hex) if current_glyph_hex else None):
        return False, f"Collision detected: codepoint \\u{normalized} is already in use by another glyph"

    return True, normalized


def register_glyph(
    workspace_dir: Path,
    glyph_id: str,
    file_ref: str,
    hex_code: Optional[str] = None,
    height: int = 8,
    ascent: int = 7,
    namespace: str = "craftlab",
    font_name: str = "default"
) -> Dict[str, Any]:
    """
    Registers or updates a bitmap glyph provider in the workspace font JSON.
    Auto-allocates the next available PUA codepoint if none is provided.
    """
    used = get_allocated_pua_hexes(workspace_dir)

    if hex_code:
        valid, result = validate_pua_hex(hex_code, used)
        if not valid:
            raise ValueError(result)
        final_hex = result
    else:
        final_hex = allocate_next_pua(used)

    final_char = chr(int(final_hex, 16))

    font_path = get_font_file_path(workspace_dir, namespace, font_name)
    font_path.parent.mkdir(parents=True, exist_ok=True)

    if font_path.exists():
        try:
            font_data = json.loads(font_path.read_text(encoding="utf-8"))
        except Exception:
            font_data = {"providers": []}
    else:
        font_data = {"providers": []}

    providers = font_data.setdefault("providers", [])

    # Remove existing provider with matching character or file
    new_providers = []
    for p in providers:
        if p.get("type") == "bitmap":
            chars = p.get("chars", [])
            has_matching_char = any(final_char in row for row in chars)
            if has_matching_char or p.get("file") == file_ref:
                continue
        new_providers.append(p)

    # Append new provider
    new_provider = {
        "type": "bitmap",
        "file": file_ref,
        "ascent": int(ascent),
        "height": int(height),
        "chars": [
            final_char
        ]
    }
    new_providers.append(new_provider)
    font_data["providers"] = new_providers

    font_path.write_text(json.dumps(font_data, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "id": glyph_id,
        "character": final_char,
        "hex": final_hex,
        "file": file_ref,
        "height": height,
        "ascent": ascent,
        "namespace": namespace,
        "font_file": font_path.name,
        "minimessage": f"<font:{namespace}:{font_name}>\\u{final_hex}</font>",
        "placeholder": f"%{namespace}_glyph_{glyph_id}%"
    }


def delete_glyph(
    workspace_dir: Path,
    hex_code: str,
    namespace: str = "craftlab",
    font_name: str = "default"
) -> bool:
    """
    Removes a glyph provider associated with a given PUA hex from the font JSON.
    """
    norm = normalize_hex(hex_code)
    target_char = chr(int(norm, 16))
    font_path = get_font_file_path(workspace_dir, namespace, font_name)
    if not font_path.exists():
        return False

    try:
        font_data = json.loads(font_path.read_text(encoding="utf-8"))
    except Exception:
        return False

    providers = font_data.get("providers", [])
    initial_len = len(providers)
    filtered = []
    for p in providers:
        if p.get("type") == "bitmap":
            chars = p.get("chars", [])
            if any(target_char in row for row in chars):
                continue
        filtered.append(p)

    if len(filtered) == initial_len:
        return False

    font_data["providers"] = filtered
    font_path.write_text(json.dumps(font_data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True
