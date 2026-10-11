import struct
import pytest
from pathlib import Path
from app.domain.sound_events import (
    parse_vorbis_header,
    probe_audio_channels,
    convert_audio_to_mono,
    load_sounds_json,
    save_sound_event,
    list_sound_events,
    delete_sound_event,
)


def create_mock_vorbis_ogg(channels: int = 1, sample_rate: int = 44100) -> bytes:
    """Creates a mock minimal Ogg Vorbis binary segment containing identification header."""
    ogg_page = b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x1e"
    vorbis_id = b"\x01vorbis" + struct.pack("<I", 0) + bytes([channels]) + struct.pack("<I", sample_rate) + b"\x00" * 16
    return ogg_page + vorbis_id


def test_parse_vorbis_header():
    mono_bytes = create_mock_vorbis_ogg(channels=1, sample_rate=44100)
    info_mono = parse_vorbis_header(mono_bytes)
    assert info_mono is not None
    assert info_mono["channels"] == 1
    assert info_mono["is_mono"] is True
    assert info_mono["sample_rate"] == 44100

    stereo_bytes = create_mock_vorbis_ogg(channels=2, sample_rate=48000)
    info_stereo = parse_vorbis_header(stereo_bytes)
    assert info_stereo is not None
    assert info_stereo["channels"] == 2
    assert info_stereo["is_mono"] is False
    assert info_stereo["sample_rate"] == 48000


def test_probe_audio_channels(tmp_path: Path):
    audio_file = tmp_path / "test_stereo.ogg"
    audio_file.write_bytes(create_mock_vorbis_ogg(channels=2, sample_rate=44100))

    probe = probe_audio_channels(audio_file)
    assert probe["channels"] == 2
    assert probe["is_mono"] is False
    assert "Stereo detected" in probe["warning"]


def test_sound_events_crud(tmp_path: Path):
    workspace = tmp_path / "workspace"

    event_payload = {
        "category": "blocks",
        "subtitle": "subtitles.craftlab.door_open",
        "sounds": [
            {"name": "craftlab:prop/door_1", "volume": 1.0, "pitch": 1.0}
        ]
    }

    saved = save_sound_event(workspace, "prop.door.open", event_payload, namespace="craftlab")
    assert saved["id"] == "prop.door.open"
    assert saved["resource_location"] == "craftlab:prop.door.open"

    # List
    events = list_sound_events(workspace)
    assert len(events) == 1
    assert events[0]["id"] == "prop.door.open"

    # Delete
    del_ok = delete_sound_event(workspace, "prop.door.open", namespace="craftlab")
    assert del_ok is True
    assert len(list_sound_events(workspace)) == 0


def test_convert_audio_to_mono_real(tmp_path: Path):
    # Test real ffmpeg conversion using a generated stereo wav -> mono ogg
    import subprocess
    import shutil

    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not available")

    # Generate small 1-second stereo tone with ffmpeg
    stereo_file = tmp_path / "generated_stereo.ogg"
    cmd_gen = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=0.2",
        "-ac", "2",
        "-c:a", "libvorbis",
        str(stereo_file)
    ]
    res_gen = subprocess.run(cmd_gen, capture_output=True)
    if res_gen.returncode != 0:
        pytest.skip("ffmpeg sine generator failed")

    probe_before = probe_audio_channels(stereo_file)
    assert probe_before["channels"] == 2

    # Downmix
    mono_output = tmp_path / "converted_mono.ogg"
    convert_audio_to_mono(stereo_file, mono_output)

    probe_after = probe_audio_channels(mono_output)
    assert probe_after["channels"] == 1
    assert probe_after["is_mono"] is True
