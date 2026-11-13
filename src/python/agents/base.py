"""
Base Agent class for auto-osint.
Provides common methods for agent execution, observation, evidence storage, and confidence updates.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import logging
import time

from ..models.evidence import Evidence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentBase(ABC):
    """
    Base agent class with common execution lifecycle methods.

    Agents can be specialized by subclassing this class and implementing
    the specific work methods (execute, observe, etc.).
    """

    def __init__(
        self,
        name: str,
        investigation_id: int,
        timeout_seconds: Optional[int] = 60,
        max_retries: int = 3,
    ):
        """
        Initialize the agent.

        Args:
            name: Agent name for logging and registry
            investigation_id: Associated investigation ID
            timeout_seconds: Maximum execution time for tool invocations
            max_retries: Maximum number of retry attempts for failed operations
        """
        self.name = name
        self.investigation_id = investigation_id
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.evidence_storage: Optional[Any] = None
        self.observation_buffer: List[Dict[str, Any]] = []

    def _execute_with_retry(
        self,
        func: Callable[[], Dict[str, Any]],
        max_retries: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute a function with automatic retry on failure.

        Args:
            func: Function to execute
            max_retries: Override of default max_retries (defaults to self.max_retries)

        Returns:
            Dict with stdout, stderr, returncode from the executed function

        Raises:
            Exception: If all retry attempts fail
        """
        if max_retries is None:
            max_retries = self.max_retries

        attempt = 0
        last_error = None

        while attempt <= max_retries:
            try:
                return func()
            except Exception as e:
                last_error = e
                attempt += 1
                if attempt <= max_retries:
                    logger.warning(
                        f"{self.name}: Attempt {attempt}/{max_retries} failed: {e}. Retrying..."
                    )
                    time.sleep(1)  # Brief delay between retries

        logger.error(f"{self.name}: All {max_retries} retries failed.")
        if last_error:
            raise last_error
        raise RuntimeError(f"{self.name}: All {max_retries} retry attempts exhausted without exception")

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's primary work.

        This method should be implemented by specific agent types.
        It should define the main investigation work for this agent.

        Args:
            context: Investigation context with target info and parameters

        Returns:
            Dict with execution results, status, and observations
        """
        pass

    def observe(self, observation: Dict[str, Any]) -> None:
        """
        Record an observation from the execution.

        Args:
            observation: Observation dict with timestamp and content
        """
        observation["timestamp"] = datetime.utcnow().isoformat()
        observation["agent"] = self.name
        self.observation_buffer.append(observation)
        logger.info(f"{self.name} observed: {observation.get('type', 'unknown')}")

    def store_evidence(
        self,
        source: str,
        claim: str,
        confidence: float,
        independence_score: float,
        independence_check_details: Optional[Dict[str, Any]] = None,
        corroborating_sources: Optional[List[int]] = None,
        contradictions: Optional[List[int]] = None,
        links: Optional[List[str]] = None,
        chain_of_custody: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """
        Store evidence in the database.

        Args:
            source: Source identifier (type, platform, document)
            claim: The finding or claim
            confidence: Confidence score (0.0-1.0, Bayesian posterior)
            independence_score: Independence score (0.0-1.0)
            independence_check_details: Details of independence tests
            corroborating_sources: List of corroborating evidence IDs
            contradictions: List of contradictory evidence IDs
            links: URLs or file paths to sources
            chain_of_custody: Immutable log of evidence collection

        Returns:
            ID of the created evidence entry
        """
        if self.evidence_storage is None:
            raise ValueError("Evidence storage not initialized. Call set_evidence_storage() first.")

        evidence = Evidence(
            source=source,
            timestamp=datetime.utcnow(),
            claim=claim,
            confidence=confidence,
            independence_score=independence_score,
            independence_check_details=independence_check_details,
            corroborating_sources=corroborating_sources or [],
            contradictions=contradictions or [],
            links=links or [],
            chain_of_custody=chain_of_custody or [],
            investigation_id=self.investigation_id,
        )

        self.evidence_storage.add(evidence)
        self.evidence_storage.commit()
        evidence_id = evidence.id

        logger.info(f"{self.name} stored evidence ID {evidence_id} for claim: {claim}")
        return evidence_id

    def update_confidence(
        self,
        evidence_id: int,
        new_confidence: float,
        new_independence_score: float,
        new_independence_check_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update confidence score for existing evidence.

        Args:
            evidence_id: ID of evidence entry to update
            new_confidence: New confidence score (0.0-1.0)
            new_independence_score: New independence score (0.0-1.0)
            new_independence_check_details: Updated independence check details
        """
        if self.evidence_storage is None:
            raise ValueError("Evidence storage not initialized. Call set_evidence_storage() first.")

        evidence = self.evidence_storage.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise ValueError(f"Evidence entry {evidence_id} not found")

        evidence.confidence = new_confidence
        evidence.independence_score = new_independence_score
        if new_independence_check_details:
            evidence.independence_check_details = new_independence_check_details

        self.evidence_storage.commit()
        logger.info(f"{self.name} updated evidence ID {evidence_id} confidence to {new_confidence}")

    def set_evidence_storage(self, storage: Any) -> None:
        """
        Set the evidence storage instance.

        Args:
            storage: SQLAlchemy session or ORM instance for evidence
        """
        self.evidence_storage = storage

    def get_observation_buffer(self) -> List[Dict[str, Any]]:
        """Return the observation buffer for this agent run."""
        return self.observation_buffer.copy()

    def reset_observation_buffer(self) -> None:
        """Clear the observation buffer."""
        self.observation_buffer = []

    def _format_confidence(self, confidence: float) -> str:
        """
        Format confidence score into human-readable level.

        Args:
            confidence: Confidence score (0.0-1.0)

        Returns:
            Confidence level string: "High", "Medium", or "Low"
        """
        if confidence >= 0.7:
            return "High"
        elif confidence >= 0.4:
            return "Medium"
        else:
            return "Low"
