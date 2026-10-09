import os
import zipfile
import hashlib
import json
from pathlib import Path
from typing import Tuple, Dict, Any


class DeterministicPackCompiler:
    """Compiles a resource pack folder into a deterministic, bit-identical ZIP archive with SHA-1 hashing."""

    FIXED_DATE_TIME = (2026, 1, 1, 0, 0, 0)
    COMPRESSION_LEVEL = 6

    @classmethod
    def compile_directory_to_zip(
        cls,
        source_dir: Path,
        output_zip_path: Path
    ) -> Tuple[str, int]:
        """
        Compiles source_dir into output_zip_path deterministically.
        Returns: (sha1_hash, file_size_in_bytes)
        """
        output_zip_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Collect all relative file paths
        rel_files = []
        for root, _, files in os.walk(source_dir):
            root_path = Path(root)
            for file_name in files:
                file_path = root_path / file_name
                rel_path = file_path.relative_to(source_dir).as_posix()
                rel_files.append((rel_path, file_path))

        # 2. Sort entries strictly lexicographically
        rel_files.sort(key=lambda x: x[0])

        # 3. Write ZIP with normalized ZipInfo
        with zipfile.ZipFile(
            output_zip_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=cls.COMPRESSION_LEVEL
        ) as zip_out:
            for rel_path, file_path in rel_files:
                content = file_path.read_bytes()

                zinfo = zipfile.ZipInfo(filename=rel_path, date_time=cls.FIXED_DATE_TIME)
                zinfo.compress_type = zipfile.ZIP_DEFLATED
                # Normalized unix file permissions (rw-r--r--)
                zinfo.external_attr = 0o644 << 16

                zip_out.writestr(zinfo, content)

        # 4. Calculate SHA-1 hash of the resulting ZIP
        sha1 = hashlib.sha1()
        with open(output_zip_path, "rb") as f:
            while chunk := f.read(65536):
                sha1.update(chunk)

        sha1_hex = sha1.hexdigest()
        file_size = output_zip_path.stat().st_size

        return sha1_hex, file_size

    @classmethod
    def generate_multiversion_mcmeta(
        cls,
        pack_format: int = 34,
        min_inclusive: int = 34,
        max_inclusive: int = 65,
        overlay_min: int = 42,
        overlay_max: int = 65,
        overlay_dir: str = "overlay_v1_21_2",
        description: str = "Universal Multi-Version Resource Pack (1.21.1 - 1.21.11)"
    ) -> Dict[str, Any]:
        """Generates pack.mcmeta with overlays for multi-version client compatibility."""
        return {
            "pack": {
                "pack_format": pack_format,
                "description": description,
                "supported_formats": {
                    "min_inclusive": min_inclusive,
                    "max_inclusive": max_inclusive
                },
                "min_format": min_inclusive,
                "max_format": max_inclusive
            },
            "overlays": {
                "entries": [
                    {
                        "formats": {
                            "min_inclusive": overlay_min,
                            "max_inclusive": overlay_max
                        },
                        "min_format": overlay_min,
                        "max_format": overlay_max,
                        "directory": overlay_dir
                    }
                ]
            }
        }

    @classmethod
    def write_multiversion_mcmeta(
        cls,
        target_dir: Path,
        pack_format: int = 34,
        description: str = "Universal Multi-Version Resource Pack (1.21.1 - 1.21.11)"
    ) -> Path:
        """Writes multi-version pack.mcmeta into target_dir."""
        mcmeta_path = target_dir / "pack.mcmeta"
        content = cls.generate_multiversion_mcmeta(pack_format=pack_format, description=description)
        mcmeta_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
        return mcmeta_path

