import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel


class ReleaseAsset(BaseModel):
    name: str
    size: int
    browser_download_url: str


class GitHubRelease(BaseModel):
    tag_name: str
    name: Optional[str] = None
    published_at: Optional[str] = None
    body: Optional[str] = None
    assets: List[ReleaseAsset] = []


def compute_file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class GitHubReleasesClient:
    def __init__(self, repo: str = "DarkBladeDev/CraftLab", token: Optional[str] = None):
        self.repo = repo
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = f"https://api.github.com/repos/{repo}/releases"

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CraftLab-Control/1.0",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    async def get_latest_release(self, client: Optional[httpx.AsyncClient] = None) -> Optional[GitHubRelease]:
        url = f"{self.base_url}/latest"
        close_client = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            close_client = True
        try:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code == 200:
                data = resp.json()
                return GitHubRelease.model_validate(data)
            return None
        finally:
            if close_client:
                await client.aclose()

    async def get_release_by_tag(
        self, tag: str, client: Optional[httpx.AsyncClient] = None
    ) -> Optional[GitHubRelease]:
        norm_tag = tag if tag.startswith("v") else f"v{tag}"
        url = f"{self.base_url}/tags/{norm_tag}"
        close_client = False
        if client is None:
            client = httpx.AsyncClient(timeout=15.0)
            close_client = True
        try:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code == 200:
                return GitHubRelease.model_validate(resp.json())
            # Also try without 'v'
            if norm_tag.startswith("v"):
                alt_url = f"{self.base_url}/tags/{norm_tag[1:]}"
                resp2 = await client.get(alt_url, headers=self._get_headers())
                if resp2.status_code == 200:
                    return GitHubRelease.model_validate(resp2.json())
            return None
        finally:
            if close_client:
                await client.aclose()

    async def download_file(
        self,
        url: str,
        dest_path: Path,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Path:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        close_client = False
        if client is None:
            client = httpx.AsyncClient(timeout=60.0)
            close_client = True
        try:
            async with client.stream("GET", url, headers=self._get_headers(), follow_redirects=True) as resp:
                resp.raise_for_status()
                with open(dest_path, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        f.write(chunk)
            return dest_path
        finally:
            if close_client:
                await client.aclose()
