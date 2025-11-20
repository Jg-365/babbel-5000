import secrets
from collections import defaultdict
from typing import Dict, List


class Metrics:
    def __init__(self):
        self.latencies: Dict[str, List[int]] = defaultdict(list)

    def create_trace_id(self) -> str:
        return secrets.token_hex(8)

    def record_latency(self, name: str, value_ms: int):
        self.latencies[name].append(value_ms)

    def percentile(self, name: str, percentile_value: float) -> float:
        series = sorted(self.latencies.get(name, []))
        if not series:
            return 0.0
        index = int(len(series) * percentile_value / 100)
        index = min(index, len(series) - 1)
        return float(series[index])
