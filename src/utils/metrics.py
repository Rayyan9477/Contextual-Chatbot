from prometheus_client import Counter, Gauge, Histogram, Summary, REGISTRY
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
# from agno.metrics import MetricsCollector
# from agno.utils import TokenManager
from config.settings import AppConfig

logger = logging.getLogger(__name__)

class Metrics:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Metrics, cls).__new__(cls)
            cls._instance._initialize_metrics()
        return cls._instance

    def _initialize_metrics(self):
        # Initialize INTERACTION_TYPES Counter
        try:
            self.INTERACTION_TYPES = Counter(
                'chat_interaction_types',
                'Count of different interaction types',
                ['type']
            )
        except ValueError:
            self.INTERACTION_TYPES = REGISTRY._names_to_collectors['chat_interaction_types']

        # Initialize RESPONSE_TIME Histogram
        try:
            self.RESPONSE_TIME = Histogram(
                'response_time_seconds',
                'Time taken to generate responses',
                buckets=[0.1, 0.5, 1, 2, 5]
            )
        except ValueError:
            self.RESPONSE_TIME = REGISTRY._names_to_collectors['response_time_seconds']

        # Initialize EMOTION_GAUGE Gauge
        try:
            self.EMOTION_GAUGE = Gauge(
                'user_emotion_intensity',
                'Intensity of detected emotions',
                ['emotion']
            )
        except ValueError:
            self.EMOTION_GAUGE = REGISTRY._names_to_collectors['user_emotion_intensity']

        # Initialize SAFETY_FLAGS Counter
        try:
            self.SAFETY_FLAGS = Counter(
                'safety_flag_triggers',
                'Count of triggered safety flags',
                ['severity_level']
            )
        except ValueError:
            self.SAFETY_FLAGS = REGISTRY._names_to_collectors['safety_flag_triggers']

        # Initialize ASSESSMENT_COMPLETED Counter
        try:
            self.ASSESSMENT_COMPLETED = Counter(
                'assessment_completed',
                'Number of completed assessments'
            )
        except ValueError:
            self.ASSESSMENT_COMPLETED = REGISTRY._names_to_collectors['assessment_completed']

        # Initialize EMBEDDING_TIME Summary
        try:
            self.EMBEDDING_TIME = Summary(
                'embedding_generation_time',
                'Time spent generating text embeddings'
            )
        except ValueError:
            self.EMBEDDING_TIME = REGISTRY._names_to_collectors['embedding_generation_time']

metrics = Metrics()

def track_metric(metric_name: str, value: float):
    if metric_name == "embedding":
        metrics.EMBEDDING_TIME.observe(value)
    elif metric_name == "response":
        metrics.RESPONSE_TIME.observe(value)
    elif metric_name == "assessment_completed":
        metrics.ASSESSMENT_COMPLETED.inc(value)
    elif metric_name == "safety_flag_raised":
        metrics.SAFETY_FLAGS.labels(severity_level="raised").inc(value)

class MetricsManager:
    """Manages metrics collection and analysis"""
    
    def __init__(self):
        self._metrics = metrics
        self._start_time = datetime.now()
        
    def track_interaction(
        self,
        interaction_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Track an interaction with metadata"""
        try:
            # Add basic metadata
            meta = {
                'timestamp': datetime.now().isoformat(),
                'interaction_type': interaction_type,
                **(metadata or {})
            }
            
            # Track latency if provided
            if 'latency' in data:
                self._metrics.RESPONSE_TIME.observe(data['latency'])
            
            # Track interaction type
            self._metrics.INTERACTION_TYPES.labels(type=interaction_type).inc()
            
            # Track emotions if present
            if 'emotions' in data:
                for emotion, intensity in data['emotions'].items():
                    self._metrics.EMOTION_GAUGE.labels(emotion=emotion).set(intensity)
            
            # Track safety flags
            if 'safety_flags' in data:
                for flag in data['safety_flags']:
                    self._metrics.SAFETY_FLAGS.labels(severity_level=flag).inc()
            
            return {
                'metrics': {
                    'latency': data.get('latency', 0),
                    'interaction_type': interaction_type,
                    'emotions': data.get('emotions', {}),
                    'safety_flags': data.get('safety_flags', [])
                },
                'metadata': meta
            }
            
        except Exception as e:
            logger.error(f"Failed to track interaction: {str(e)}")
            return {}
            
    def get_metrics_summary(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        interaction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        try:
            start = datetime.fromisoformat(start_time) if start_time else self._start_time
            end = datetime.fromisoformat(end_time) if end_time else datetime.now()
            
            # Get metrics from Prometheus
            summary = {
                'total_interactions': self._metrics.INTERACTION_TYPES._value.sum(),
                'avg_response_time': float(self._metrics.RESPONSE_TIME.describe()['avg']),
                'total_safety_flags': self._metrics.SAFETY_FLAGS._value.sum(),
                'total_assessments': self._metrics.ASSESSMENT_COMPLETED._value,
                'time_range': {
                    'start': start.isoformat(),
                    'end': end.isoformat()
                }
            }
            
            # Add emotion summaries if available
            emotions = {}
            for emotion in self._metrics.EMOTION_GAUGE._metrics:
                emotions[emotion] = float(self._metrics.EMOTION_GAUGE.labels(emotion=emotion)._value)
            if emotions:
                summary['emotions'] = emotions
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {str(e)}")
            return {}
            
    def track_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track an error occurrence"""
        try:
            self.collector.add_error(
                error_type=error_type,
                message=error_message,
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'context': context or {}
                }
            )
        except Exception as e:
            logger.error(f"Failed to track error: {str(e)}")
            
    def get_error_summary(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary of tracked errors"""
        try:
            # Get filtered errors
            errors = self.collector.get_errors(
                start_time=start_time,
                end_time=end_time
            )
            
            # Group by error type
            error_counts = {}
            for error in errors:
                error_type = error['error_type']
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
            return {
                'total_errors': len(errors),
                'error_types': error_counts,
                'time_range': {
                    'start': start_time or min(e['metadata']['timestamp'] for e in errors) if errors else None,
                    'end': end_time or max(e['metadata']['timestamp'] for e in errors) if errors else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get error summary: {str(e)}")
            return {}