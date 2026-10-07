import json
from typing import Dict, Any, Optional
import httpx


class RemoteControlClient:
    def __init__(self, server_url: str, token: Optional[str] = None):
        self.server_url = server_url.rstrip("/")
        self.token = token
        self._headers = {}
        if self.token:
            self._headers["Authorization"] = f"Bearer {self.token}"

    async def get_status(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self._headers, timeout=10.0) as client:
            resp = await client.get(f"{self.server_url}/api/v1/status")
            resp.raise_for_status()
            return resp.json()

    async def get_metrics(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self._headers, timeout=10.0) as client:
            resp = await client.get(f"{self.server_url}/api/v1/metrics")
            resp.raise_for_status()
            return resp.json()

    async def get_doctor(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self._headers, timeout=15.0) as client:
            resp = await client.get(f"{self.server_url}/api/v1/doctor")
            resp.raise_for_status()
            return resp.json()

    async def execute_lifecycle(self, action: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self._headers, timeout=30.0) as client:
            resp = await client.post(f"{self.server_url}/api/v1/lifecycle/{action}")
            resp.raise_for_status()
            return resp.json()

    async def get_releases(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self._headers, timeout=10.0) as client:
            resp = await client.get(f"{self.server_url}/api/v1/update/releases")
            resp.raise_for_status()
            return resp.json()

    async def check_updates(self, repo: Optional[str] = None) -> Dict[str, Any]:
        params = {"repo": repo} if repo else {}
        async with httpx.AsyncClient(headers=self._headers, timeout=15.0) as client:
            resp = await client.get(f"{self.server_url}/api/v1/update/check", params=params)
            resp.raise_for_status()
            return resp.json()

    async def prepare_update(
        self,
        version: str,
        github_repo: Optional[str] = None,
        local_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"version": version}
        if github_repo:
            payload["github_repo"] = github_repo
        if local_file:
            payload["local_file"] = local_file
        async with httpx.AsyncClient(headers=self._headers, timeout=120.0) as client:
            resp = await client.post(f"{self.server_url}/api/v1/update/prepare", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def apply_update(
        self,
        version: str,
        timeout: int = 15,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> Dict[str, Any]:
        payload = {
            "version": version,
            "timeout": timeout,
            "host": host,
            "port": port,
        }
        async with httpx.AsyncClient(headers=self._headers, timeout=60.0) as client:
            resp = await client.post(f"{self.server_url}/api/v1/update/apply", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def rollback(
        self,
        target_version: Optional[str] = None,
        timeout: int = 15,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> Dict[str, Any]:
        payload = {
            "target_version": target_version,
            "timeout": timeout,
            "host": host,
            "port": port,
        }
        async with httpx.AsyncClient(headers=self._headers, timeout=60.0) as client:
            resp = await client.post(f"{self.server_url}/api/v1/update/rollback", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def get_maintenance(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(headers=self._headers, timeout=10.0) as client:
            resp = await client.get(f"{self.server_url}/api/v1/update/maintenance")
            resp.raise_for_status()
            return resp.json()

    async def set_maintenance(
        self,
        enable: Optional[bool] = None,
        message: str = "",
    ) -> Dict[str, Any]:
        payload = {"enable": enable, "message": message}
        async with httpx.AsyncClient(headers=self._headers, timeout=10.0) as client:
            resp = await client.post(f"{self.server_url}/api/v1/update/maintenance", json=payload)
            resp.raise_for_status()
            return resp.json()

