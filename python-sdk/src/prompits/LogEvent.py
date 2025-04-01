from dataclasses import dataclass
from datetime import datetime

@dataclass
class LogEvent:
    """Class representing a log event."""
    pit_name: str
    level: str
    message: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self):
        """Convert the log event to a dictionary."""
        return {
            "pit_name": self.pit_name,
            "level": self.level,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }

    def __str__(self):
        """String representation of the log event."""
        return f"{self.timestamp} - {self.pit_name} - {self.level} - {self.message}" 