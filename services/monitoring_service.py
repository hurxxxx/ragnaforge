"""Simplified monitoring service for duplicate detection and system performance."""

import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import Counter
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class DuplicateEvent:
    """Data class for duplicate detection events."""
    timestamp: float
    file_hash: str
    filename: str
    file_size: int
    upload_count: int
    storage_saved_bytes: int


@dataclass
class PerformanceMetrics:
    """Data class for performance metrics."""
    timestamp: float
    operation: str
    duration_ms: float
    success: bool
    error_message: Optional[str] = None


class MonitoringService:
    """Simplified monitoring service for duplicate detection and system performance."""

    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage for recent events (reduced size)
        self.duplicate_events: List[DuplicateEvent] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        self.max_memory_events = 100  # Reduced from 1000

        logger.info(f"Monitoring service initialized with log_dir: {log_dir}")
    
    def log_duplicate_event(self,
                          file_hash: str,
                          filename: str,
                          file_size: int,
                          upload_count: int):
        """Log a duplicate detection event."""

        # Calculate storage saved (all uploads after the first one)
        storage_saved = file_size * (upload_count - 1) if upload_count > 1 else 0

        event = DuplicateEvent(
            timestamp=time.time(),
            file_hash=file_hash,
            filename=filename,
            file_size=file_size,
            upload_count=upload_count,
            storage_saved_bytes=storage_saved
        )

        # Add to memory storage
        self.duplicate_events.append(event)

        # Keep only recent events in memory
        if len(self.duplicate_events) > self.max_memory_events:
            self.duplicate_events = self.duplicate_events[-self.max_memory_events:]

        # Log to file
        self._write_event_to_file("duplicates", event)

        logger.info(f"Duplicate event logged: {filename} (count: {upload_count}, saved: {storage_saved} bytes)")
    
    def log_performance_metric(self,
                             operation: str,
                             duration_ms: float,
                             success: bool = True,
                             error_message: Optional[str] = None):
        """Log a performance metric."""

        metric = PerformanceMetrics(
            timestamp=time.time(),
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )

        # Add to memory storage
        self.performance_metrics.append(metric)

        # Keep only recent metrics in memory
        if len(self.performance_metrics) > self.max_memory_events:
            self.performance_metrics = self.performance_metrics[-self.max_memory_events:]

        # Log to file
        self._write_event_to_file("performance", metric)

        if not success:
            logger.warning(f"Performance issue logged: {operation} failed in {duration_ms:.1f}ms - {error_message}")
    
    def get_duplicate_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get simplified duplicate detection statistics."""

        cutoff_time = time.time() - (hours * 3600)
        recent_events = [e for e in self.duplicate_events if e.timestamp >= cutoff_time]

        if not recent_events:
            return {
                "period_hours": hours,
                "total_duplicates": 0,
                "storage_saved_bytes": 0,
                "storage_saved_mb": 0
            }

        # Calculate basic statistics
        total_duplicates = len(recent_events)
        total_storage_saved = sum(e.storage_saved_bytes for e in recent_events)

        return {
            "period_hours": hours,
            "total_duplicates": total_duplicates,
            "storage_saved_bytes": total_storage_saved,
            "storage_saved_mb": round(total_storage_saved / (1024 * 1024), 2)
        }
    
    def get_performance_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get simplified performance statistics."""

        cutoff_time = time.time() - (hours * 3600)
        recent_metrics = [m for m in self.performance_metrics if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {
                "period_hours": hours,
                "total_operations": 0,
                "success_rate": 0,
                "average_duration_ms": 0
            }

        # Calculate basic statistics
        total_operations = len(recent_metrics)
        successful_operations = sum(1 for m in recent_metrics if m.success)
        success_rate = (successful_operations / total_operations) * 100
        average_duration = sum(m.duration_ms for m in recent_metrics) / total_operations

        return {
            "period_hours": hours,
            "total_operations": total_operations,
            "success_rate": round(success_rate, 2),
            "average_duration_ms": round(average_duration, 2)
        }
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic monitoring statistics."""

        duplicate_stats = self.get_duplicate_statistics(hours=24)
        performance_stats = self.get_performance_statistics(hours=24)

        return {
            "duplicate_detection": duplicate_stats,
            "performance": performance_stats,
            "system_info": {
                "memory_events_count": len(self.duplicate_events),
                "memory_metrics_count": len(self.performance_metrics)
            }
        }

    def _write_event_to_file(self, event_type: str, event_data):
        """Write event to log file."""
        try:
            # Create daily log files
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"{event_type}_{date_str}.jsonl"

            # Convert dataclass to dict
            data = asdict(event_data)

            # Append to file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")

        except Exception as e:
            logger.error(f"Failed to write event to file: {e}")

    def cleanup_old_logs(self, days_to_keep: int = 7):
        """Clean up old log files (reduced default retention)."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            for log_file in self.log_dir.glob("*.jsonl"):
                try:
                    date_part = log_file.stem.split("_")[-1]
                    file_date = datetime.strptime(date_part, "%Y-%m-%d")

                    if file_date < cutoff_date:
                        log_file.unlink()
                        logger.info(f"Deleted old log file: {log_file}")

                except (ValueError, IndexError):
                    continue

        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")


# Global service instance
monitoring_service = MonitoringService()
