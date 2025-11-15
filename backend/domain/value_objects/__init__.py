"""
Value objects package.

Contains immutable value objects that are identified by their attributes.
"""

from .session_reference import SessionReference
from .vote_position import VotePosition
from .legislature import Legislature
from .confidence_score import ConfidenceScore

__all__ = [
    'SessionReference',
    'VotePosition',
    'Legislature',
    'ConfidenceScore',
]
