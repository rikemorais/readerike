"""IJobRepository — abstract interface for job persistence."""

from abc import ABC, abstractmethod

from readerike.core.entities.job import Job


class IJobRepository(ABC):
    """Port for persisting and retrieving Job entities."""

    @abstractmethod
    async def save(self, job: Job) -> Job:
        """Persist a job and return it."""
        ...

    @abstractmethod
    async def find_by_id(self, job_id: str) -> Job | None:
        """Return a job by its ID, or None if not found."""
        ...

    @abstractmethod
    async def find_all(self) -> list[Job]:
        """Return all jobs ordered by created_at descending."""
        ...

    @abstractmethod
    async def delete(self, job_id: str) -> None:
        """Delete a job by its ID."""
        ...
