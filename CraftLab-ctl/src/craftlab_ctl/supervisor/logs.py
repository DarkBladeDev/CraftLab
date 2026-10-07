import os
import asyncio
from collections import deque
from pathlib import Path
from typing import List, AsyncIterator, Optional


class LogRingBuffer:
    def __init__(self, max_lines: int = 1000):
        self.max_lines = max_lines
        self._buffer: deque = deque(maxlen=max_lines)
        self._subscribers: List[asyncio.Queue] = []

    def append(self, line: str) -> None:
        clean_line = line.rstrip("\r\n")
        self._buffer.append(clean_line)
        for q in list(self._subscribers):
            try:
                q.put_nowait(clean_line)
            except Exception:
                pass

    def get_recent(self, n: int = 100) -> List[str]:
        lines = list(self._buffer)
        return lines[-n:] if n < len(lines) else lines

    async def subscribe(self) -> AsyncIterator[str]:
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._subscribers.append(q)
        try:
            while True:
                line = await q.get()
                yield line
        finally:
            if q in self._subscribers:
                self._subscribers.remove(q)


async def tail_file_to_buffer(file_path: Path, ring_buffer: LogRingBuffer, stop_event: asyncio.Event) -> None:
    """Tails a log file and pushes new lines into the ring buffer."""
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()

    # Pre-populate with existing lines if any
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f.readlines()[-200:]:
                ring_buffer.append(line)
    except Exception:
        pass

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, os.SEEK_END)
        while not stop_event.is_set():
            line = f.readline()
            if line:
                ring_buffer.append(line)
            else:
                await asyncio.sleep(0.2)
