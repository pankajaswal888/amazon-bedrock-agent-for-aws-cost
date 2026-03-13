from contextlib import contextmanager
import logging
import time
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}

    @contextmanager
    def measure_time(self, operation_name: str):
        """Context manager to measure operation duration"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if operation_name not in self.metrics:
                self.metrics[operation_name] = []
            self.metrics[operation_name].append(duration)
            logger.info(f"Operation '{operation_name}' took {duration:.2f} seconds")

    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of performance metrics"""
        summary = {}
        for operation, durations in self.metrics.items():
            if durations:
                summary[operation] = {
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "count": len(durations),
                }
        return summary
