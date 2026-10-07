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
