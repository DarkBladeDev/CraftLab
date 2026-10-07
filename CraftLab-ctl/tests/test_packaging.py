import json
import tarfile
from pathlib import Path
import pytest

from scripts.build_release import (
    compute_sha256,
    build_release_manifest,
    create_release_package,
)


def test_compute_sha256(tmp_path: Path):
    sample = tmp_path / "hello.txt"
    sample.write_text("craftlab test payload", encoding="utf-8")
    sha = compute_sha256(sample)
    assert len(sha) == 64
    assert isinstance(sha, str)


def test_build_release_manifest():
    manifest = build_release_manifest(
        version="v1.2.3",
        git_commit="abcdef123456",
        requires_craftctl=">=0.1.0",
        requires_python=">=3.11",
        database_version=2,
        checksums={"backend/main.py": "dummy"},
    )
    assert manifest["name"] == "craftlab"
    assert manifest["version"] == "1.2.3"
    assert manifest["git_commit"] == "abcdef123456"
    assert manifest["requires_craftctl"] == ">=0.1.0"
    assert manifest["requires_python"] == ">=3.11"
    assert manifest["database_version"] == 2
    assert "backend/main.py" in manifest["checksums"]
    assert "built_at" in manifest


def test_create_release_package_mock(tmp_path: Path):
    # Setup mock repo structure
    repo = tmp_path / "mock_repo"
    repo.mkdir()

    backend_dir = repo / "backend"
    backend_dir.mkdir()
    (backend_dir / "main.py").write_text("# main", encoding="utf-8")
    (backend_dir / "requirements.txt").write_text("fastapi>=0.100.0\n", encoding="utf-8")
    app_dir = backend_dir / "app"
    app_dir.mkdir()
    (app_dir / "server.py").write_text("# server", encoding="utf-8")

    frontend_dist = repo / "frontend" / "dist"
    frontend_dist.mkdir(parents=True)
    (frontend_dist / "index.html").write_text("<html><body>CraftLab</body></html>", encoding="utf-8")

    out_dir = tmp_path / "dist"

    tar_path = create_release_package(
        repo_root=repo,
        version="1.5.0",
        output_dir=out_dir,
        skip_frontend_build=True,
        git_commit="testcommithash",
    )

    assert tar_path.exists()
    assert tar_path.name == "craftlab-v1.5.0.tar.gz"

    sha_file = out_dir / "craftlab-v1.5.0.tar.gz.sha256"
    assert sha_file.exists()
    content = sha_file.read_text(encoding="utf-8")
    expected_sha = compute_sha256(tar_path)
    assert expected_sha in content

    # Inspect tarball contents
    with tarfile.open(tar_path, "r:gz") as tar:
        names = tar.getnames()
        assert "manifest.json" in names
        assert "backend/main.py" in names
        assert "backend/requirements.txt" in names
        assert "backend/app/server.py" in names
        assert "frontend_dist/index.html" in names

        # Read manifest from tar
        manifest_f = tar.extractfile("manifest.json")
        assert manifest_f is not None
        manifest_obj = json.load(manifest_f)
        assert manifest_obj["version"] == "1.5.0"
        assert manifest_obj["git_commit"] == "testcommithash"
        assert "backend/main.py" in manifest_obj["checksums"]
