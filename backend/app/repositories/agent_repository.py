"""Repository for Agent CRUD operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentRepository:
    """Database access layer for the Agent model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, data: AgentCreate) -> Agent:
        """Create and persist a new Agent for *user_id*.

        Args:
            user_id: UUID of the owning user.
            data: Validated creation payload.

        Returns:
            The newly created Agent instance.
        """
        agent = Agent(
            user_id=user_id,
            name=data.name,
            description=data.description,
        )
        self.db.add(agent)
        await self.db.flush()
        await self.db.refresh(agent)
        return agent

    async def get_by_id(self, agent_id: uuid.UUID) -> Agent | None:
        """Fetch a single Agent by primary key.

        Args:
            agent_id: UUID of the Agent.

        Returns:
            The Agent or *None* if not found.
        """
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalars().first()

    async def get_by_id_and_user(
        self, agent_id: uuid.UUID, user_id: uuid.UUID
    ) -> Agent | None:
        """Fetch a single Agent verifying ownership.

        Args:
            agent_id: UUID of the Agent.
            user_id: UUID of the requesting user.

        Returns:
            The Agent or *None* if not found or not owned by *user_id*.
        """
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id)
        )
        return result.scalars().first()

    async def list_by_user(self, user_id: uuid.UUID) -> list[Agent]:
        """Return all Agents owned by *user_id*, ordered by creation time.

        Args:
            user_id: UUID of the owning user.

        Returns:
            List of Agent instances.
        """
        result = await self.db.execute(
            select(Agent).where(Agent.user_id == user_id).order_by(Agent.created_at)
        )
        return list(result.scalars().all())

    async def update(self, agent: Agent, data: AgentUpdate) -> Agent:
        """Apply non-null fields from *data* onto *agent* and flush.

        Args:
            agent: Existing Agent ORM instance.
            data: Validated update payload.

        Returns:
            The updated Agent instance.
        """
        if data.name is not None:
            agent.name = data.name
        if data.description is not None:
            agent.description = data.description
        await self.db.flush()
        await self.db.refresh(agent)
        return agent

    async def delete(self, agent: Agent) -> None:
        """Delete *agent* from the database.

        Args:
            agent: The Agent instance to delete.
        """
        await self.db.delete(agent)
        await self.db.flush()
