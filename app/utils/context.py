from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional


class ContextMemory:
    def __init__(self, window: int = 10):
        self.window = window
        self.storage: Dict[str, Deque[dict]] = defaultdict(deque)

    def append(self, session_id: Optional[str], role: str, text: str, lang: str):
        if not session_id:
            return
        buffer = self.storage[session_id]
        buffer.append({"role": role, "text": text, "lang": lang})
        while len(buffer) > self.window:
            buffer.popleft()

    def get(self, session_id: Optional[str]) -> Optional[List[dict]]:
        if not session_id:
            return None
        if session_id not in self.storage:
            return []
        return list(self.storage[session_id])

    def clear(self, session_id: str):
        if session_id in self.storage:
            del self.storage[session_id]
