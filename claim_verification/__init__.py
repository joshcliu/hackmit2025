"""
Claim Verification System

A parallel agent-based system for verifying political claims using 
specialized search agents and an orchestrator for synthesis.
"""

from claim_verification.orchestrator import ClaimVerificationOrchestrator, VerificationResult
from claim_verification.base_agent import AgentOutput, SourceInfo

__all__ = [
    "ClaimVerificationOrchestrator",
    "VerificationResult",
    "AgentOutput",
    "SourceInfo"
]

__version__ = "0.1.0"
