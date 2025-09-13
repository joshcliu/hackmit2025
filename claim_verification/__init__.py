"""
Claim Verification System

A parallel agent-based system for verifying political claims using 
specialized search agents and an orchestrator for synthesis.
"""

from .orchestrator import ClaimVerificationOrchestrator
from .base_agent import AgentOutput, SourceInfo

__all__ = [
    "ClaimVerificationOrchestrator",
    "AgentOutput",
    "SourceInfo"
]

__version__ = "0.1.0"
