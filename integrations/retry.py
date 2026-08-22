"""Deterministic retry/backoff policy for reference integration delivery."""

from __future__ import annotations

from dataclasses import dataclass


class RetryableTransportError(RuntimeError):
    """Raised by a local transport stub for retryable failures."""


class NonRetryableTransportError(RuntimeError):
    """Raised for validation/auth/contract failures that should not be retried."""


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Retry policy that calculates metadata and never sleeps in tests."""

    max_attempts: int = 3
    base_delay_seconds: int = 30
    max_delay_seconds: int = 300

    def backoff_seconds(self, attempt: int) -> int:
        """Calculate bounded exponential backoff for the next attempt."""
        if attempt < 1:
            return 0
        return min(self.base_delay_seconds * (2 ** (attempt - 1)), self.max_delay_seconds)

    def should_retry(self, *, attempt: int, error: Exception) -> bool:
        """Return whether another attempt should be scheduled."""
        return isinstance(error, RetryableTransportError) and attempt < self.max_attempts


__all__ = ["NonRetryableTransportError", "RetryPolicy", "RetryableTransportError"]
