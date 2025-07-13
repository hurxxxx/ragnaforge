"""Monitoring and analytics service for duplicate detection and system performance."""

import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class DuplicateEvent:
    """Data class for duplicate detection events."""
    timestamp: float
    file_hash: str
    filename: str
    file_size: int
    file_type: str
    upload_count: int
    storage_saved_bytes: int
    detection_method: str  # 'hash', 'cache', 'database'


@dataclass
class PerformanceMetrics:
    """Data class for performance metrics."""
    timestamp: float
    operation: str  # 'upload', 'hash_calculation', 'duplicate_check', etc.
    duration_ms: float
    file_size_bytes: int
    success: bool
    error_message: Optional[str] = None


class MonitoringService:
    """Service for monitoring duplicate detection and system performance."""
    
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory storage for recent events (last 1000 events)
        self.duplicate_events: List[DuplicateEvent] = []
        self.performance_metrics: List[PerformanceMetrics] = []
        self.max_memory_events = 1000
        
        # Statistics cache
        self._stats_cache = {}
        self._cache_expiry = 0
        self._cache_duration = 300  # 5 minutes
        
        logger.info(f"Monitoring service initialized with log_dir: {log_dir}")
    
    def log_duplicate_event(self, 
                          file_hash: str,
                          filename: str,
                          file_size: int,
                          file_type: str,
                          upload_count: int,
                          detection_method: str = "hash"):
        """Log a duplicate detection event."""
        
        # Calculate storage saved (all uploads after the first one)
        storage_saved = file_size * (upload_count - 1) if upload_count > 1 else 0
        
        event = DuplicateEvent(
            timestamp=time.time(),
            file_hash=file_hash,
            filename=filename,
            file_size=file_size,
            file_type=file_type,
            upload_count=upload_count,
            storage_saved_bytes=storage_saved,
            detection_method=detection_method
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
                             file_size_bytes: int = 0,
                             success: bool = True,
                             error_message: Optional[str] = None):
        """Log a performance metric."""
        
        metric = PerformanceMetrics(
            timestamp=time.time(),
            operation=operation,
            duration_ms=duration_ms,
            file_size_bytes=file_size_bytes,
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
        """Get duplicate detection statistics for the specified time period."""
        
        # Check cache first
        cache_key = f"duplicate_stats_{hours}"
        if (cache_key in self._stats_cache and 
            time.time() < self._cache_expiry):
            return self._stats_cache[cache_key]
        
        cutoff_time = time.time() - (hours * 3600)
        recent_events = [e for e in self.duplicate_events if e.timestamp >= cutoff_time]
        
        if not recent_events:
            return {
                "period_hours": hours,
                "total_duplicates": 0,
                "unique_files": 0,
                "storage_saved_bytes": 0,
                "storage_saved_mb": 0,
                "detection_methods": {},
                "file_types": {},
                "top_duplicated_files": [],
                "hourly_distribution": {}
            }
        
        # Calculate statistics
        total_duplicates = len(recent_events)
        unique_files = len(set(e.file_hash for e in recent_events))
        total_storage_saved = sum(e.storage_saved_bytes for e in recent_events)
        
        # Detection methods distribution
        detection_methods = Counter(e.detection_method for e in recent_events)
        
        # File types distribution
        file_types = Counter(e.file_type for e in recent_events)
        
        # Top duplicated files
        file_duplicates = defaultdict(list)
        for event in recent_events:
            file_duplicates[event.file_hash].append(event)
        
        top_duplicated = sorted(
            file_duplicates.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        
        top_duplicated_files = []
        for file_hash, events in top_duplicated:
            latest_event = max(events, key=lambda e: e.timestamp)
            top_duplicated_files.append({
                "file_hash": file_hash[:16] + "...",
                "filename": latest_event.filename,
                "duplicate_count": len(events),
                "total_storage_saved": sum(e.storage_saved_bytes for e in events),
                "file_size": latest_event.file_size
            })
        
        # Hourly distribution
        hourly_dist = defaultdict(int)
        for event in recent_events:
            hour = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d %H:00")
            hourly_dist[hour] += 1
        
        stats = {
            "period_hours": hours,
            "total_duplicates": total_duplicates,
            "unique_files": unique_files,
            "storage_saved_bytes": total_storage_saved,
            "storage_saved_mb": round(total_storage_saved / (1024 * 1024), 2),
            "detection_methods": dict(detection_methods),
            "file_types": dict(file_types),
            "top_duplicated_files": top_duplicated_files,
            "hourly_distribution": dict(hourly_dist),
            "generated_at": time.time()
        }
        
        # Cache the results
        self._stats_cache[cache_key] = stats
        self._cache_expiry = time.time() + self._cache_duration
        
        return stats
    
    def get_performance_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance statistics for the specified time period."""
        
        cutoff_time = time.time() - (hours * 3600)
        recent_metrics = [m for m in self.performance_metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {
                "period_hours": hours,
                "total_operations": 0,
                "success_rate": 0,
                "average_duration_ms": 0,
                "operations": {},
                "error_summary": {}
            }
        
        # Calculate statistics
        total_operations = len(recent_metrics)
        successful_operations = sum(1 for m in recent_metrics if m.success)
        success_rate = (successful_operations / total_operations) * 100
        
        # Average duration by operation
        operation_stats = defaultdict(list)
        for metric in recent_metrics:
            operation_stats[metric.operation].append(metric.duration_ms)
        
        operations = {}
        for op, durations in operation_stats.items():
            operations[op] = {
                "count": len(durations),
                "avg_duration_ms": round(sum(durations) / len(durations), 2),
                "min_duration_ms": round(min(durations), 2),
                "max_duration_ms": round(max(durations), 2)
            }
        
        # Error summary
        error_metrics = [m for m in recent_metrics if not m.success]
        error_summary = Counter(m.operation for m in error_metrics)
        
        return {
            "period_hours": hours,
            "total_operations": total_operations,
            "success_rate": round(success_rate, 2),
            "average_duration_ms": round(sum(m.duration_ms for m in recent_metrics) / total_operations, 2),
            "operations": operations,
            "error_summary": dict(error_summary),
            "generated_at": time.time()
        }
    
    def _write_event_to_file(self, event_type: str, event_data):
        """Write event to log file."""
        try:
            # Create daily log files
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"{event_type}_{date_str}.jsonl"
            
            # Convert dataclass to dict
            if hasattr(event_data, '__dict__'):
                data = asdict(event_data)
            else:
                data = event_data
            
            # Append to file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to write event to file: {e}")
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for log_file in self.log_dir.glob("*.jsonl"):
                # Extract date from filename
                try:
                    date_part = log_file.stem.split("_")[-1]  # Get last part after underscore
                    file_date = datetime.strptime(date_part, "%Y-%m-%d")
                    
                    if file_date < cutoff_date:
                        log_file.unlink()
                        logger.info(f"Deleted old log file: {log_file}")
                        
                except (ValueError, IndexError):
                    # Skip files that don't match expected format
                    continue
                    
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
    
    def export_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Export comprehensive statistics for the specified period."""
        
        duplicate_stats = self.get_duplicate_statistics(hours)
        performance_stats = self.get_performance_statistics(hours)
        
        return {
            "export_timestamp": time.time(),
            "period_hours": hours,
            "duplicate_detection": duplicate_stats,
            "performance": performance_stats,
            "system_info": {
                "memory_events_count": len(self.duplicate_events),
                "memory_metrics_count": len(self.performance_metrics),
                "log_directory": str(self.log_dir)
            }
        }


# Global service instance
monitoring_service = MonitoringService()
