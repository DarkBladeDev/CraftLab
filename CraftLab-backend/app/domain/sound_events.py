import json
import os
import struct
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union

VALID_SOUND_CATEGORIES = {
    "master",
    "music",
    "record",
    "weather",
    "block",
    "blocks",
    "hostile",
    "neutral",
    "player",
    "ambient",
    "voice"
}


def get_sounds_json_path(workspace_dir: Path, namespace: str = "craftlab") -> Path:
    return workspace_dir / "assets" / namespace / "sounds.json"


def load_sounds_json(workspace_dir: Path, namespace: str = "craftlab") -> Dict[str, Any]:
    path = get_sounds_json_path(workspace_dir, namespace)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_sounds_json(workspace_dir: Path, data: Dict[str, Any], namespace: str = "craftlab") -> Path:
    path = get_sounds_json_path(workspace_dir, namespace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def parse_vorbis_header(file_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    Parses Ogg Vorbis identification header to extract channel count and sample rate.
    """
    vorbis_sig = b"\x01vorbis"
    idx = file_bytes.find(vorbis_sig)
    if idx == -1:
        return None

    # Vorbis ID packet format:
    # 0..6:   \x01vorbis
    # 7..10:  vorbis_version (uint32)
    # 11:     audio_channels (uint8)
    # 12..15: audio_sample_rate (uint32)
    offset = idx + len(vorbis_sig) + 4
    if len(file_bytes) < offset + 5:
        return None

    channels = file_bytes[offset]
    sample_rate = struct.unpack("<I", file_bytes[offset + 1 : offset + 5])[0]

    return {
        "channels": int(channels),
        "is_mono": channels == 1,
        "sample_rate": int(sample_rate),
        "format": "ogg_vorbis"
    }


def probe_audio_channels(file_path: Path) -> Dict[str, Any]:
    """
    Inspects audio file to determine channel count (Mono vs Stereo) and spatial readiness.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    file_bytes = file_path.read_bytes()

    # Fast Ogg Vorbis binary inspection
    parsed = parse_vorbis_header(file_bytes)
    if parsed:
        channels = parsed["channels"]
        sample_rate = parsed["sample_rate"]
        is_mono = channels == 1
        warning = None if is_mono else "2-channel Stereo detected. Stereo audio bypasses 3D distance attenuation in Minecraft."
        return {
            "channels": channels,
            "is_mono": is_mono,
            "sample_rate": sample_rate,
            "format": "ogg",
            "warning": warning,
            "file_size": len(file_bytes)
        }

    # Fallback to ffprobe if available
    ffprobe_cmd = shutil.which("ffprobe")
    if ffprobe_cmd:
        try:
            res = subprocess.run(
                [ffprobe_cmd, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels,sample_rate", "-of", "json", str(file_path)],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(res.stdout)
            streams = data.get("streams", [])
            if streams:
                ch = int(streams[0].get("channels", 1))
                sr = int(streams[0].get("sample_rate", 44100))
                is_mono = ch == 1
                return {
                    "channels": ch,
                    "is_mono": is_mono,
                    "sample_rate": sr,
                    "format": file_path.suffix.lstrip("."),
                    "warning": None if is_mono else "2-channel Stereo detected. Stereo audio bypasses 3D distance attenuation in Minecraft.",
                    "file_size": len(file_bytes)
                }
        except Exception:
            pass

    # Default fallback assumption
    return {
        "channels": 1,
        "is_mono": True,
        "sample_rate": 44100,
        "format": file_path.suffix.lstrip("."),
        "warning": None,
        "file_size": len(file_bytes)
    }


def convert_audio_to_mono(input_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Downmixes multi-channel audio into a 1-channel Mono OGG Vorbis file using ffmpeg.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {input_path}")

    target = output_path if output_path else input_path
    temp_target = target.with_suffix(".mono.tmp.ogg")

    ffmpeg_cmd = shutil.which("ffmpeg")
    if not ffmpeg_cmd:
        raise RuntimeError("ffmpeg binary not found in system PATH. Cannot downmix audio.")

    cmd = [
        ffmpeg_cmd,
        "-y",
        "-i", str(input_path),
        "-ac", "1",
        "-c:a", "libvorbis",
        "-q:a", "4",
        str(temp_target)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if temp_target.exists():
            temp_target.unlink()
        raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")

    shutil.move(str(temp_target), str(target))
    return target


def list_sound_events(workspace_dir: Path, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    assets_dir = workspace_dir / "assets"
    if not assets_dir.exists():
        return results

    namespaces = [assets_dir / namespace] if namespace else [d for d in assets_dir.iterdir() if d.is_dir()]

    for ns_dir in namespaces:
        ns_name = ns_dir.name
        sounds_path = ns_dir / "sounds.json"
        if not sounds_path.exists():
            continue

        data = load_sounds_json(workspace_dir, ns_name)
        for event_id, event_info in data.items():
            results.append({
                "id": event_id,
                "namespace": ns_name,
                "resource_location": f"{ns_name}:{event_id}",
                "category": event_info.get("category", "master"),
                "subtitle": event_info.get("subtitle"),
                "sounds": event_info.get("sounds", []),
                "file_path": str(sounds_path.relative_to(workspace_dir)).replace("\\", "/")
            })

    return results


def save_sound_event(
    workspace_dir: Path,
    event_id: str,
    event_data: Dict[str, Any],
    namespace: str = "craftlab"
) -> Dict[str, Any]:
    if ":" in event_id:
        parsed_ns, parsed_id = event_id.split(":", 1)
        if parsed_ns.strip():
            namespace = parsed_ns.strip()
        event_id = parsed_id.strip()

    sounds = load_sounds_json(workspace_dir, namespace)

    category = event_data.get("category", "master")
    if category not in VALID_SOUND_CATEGORIES:
        category = "master"

    normalized_event = {
        "category": category,
        "sounds": event_data.get("sounds", [])
    }
    if event_data.get("subtitle"):
        normalized_event["subtitle"] = event_data["subtitle"]

    sounds[event_id] = normalized_event
    save_sounds_json(workspace_dir, sounds, namespace)

    return {
        "id": event_id,
        "namespace": namespace,
        "resource_location": f"{namespace}:{event_id}",
        **normalized_event
    }


def delete_sound_event(workspace_dir: Path, event_id: str, namespace: str = "craftlab") -> bool:
    if ":" in event_id:
        parsed_ns, parsed_id = event_id.split(":", 1)
        if parsed_ns.strip():
            namespace = parsed_ns.strip()
        event_id = parsed_id.strip()

    sounds = load_sounds_json(workspace_dir, namespace)
    if event_id in sounds:
        del sounds[event_id]
        save_sounds_json(workspace_dir, sounds, namespace)
        return True
    return False
