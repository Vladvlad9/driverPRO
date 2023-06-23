from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update, delete, and_

from models import Event, create_async_session
from schemas import EventInDBSchema, EventSchema


class CRUDEvent(object):

    @staticmethod
    @create_async_session
    async def add(event: EventSchema, session: AsyncSession = None) -> EventInDBSchema | None:
        events = Event(
            **event.dict()
        )
        session.add(events)
        try:
            await session.commit()
        except IntegrityError as e:
            print(e)
        else:
            await session.refresh(events)
            return EventInDBSchema(**events.__dict__)

    @staticmethod
    @create_async_session
    async def delete(event_id: int, session: AsyncSession = None) -> None:
        await session.execute(
            delete(Event)
            .where(Event.id == event_id)
        )
        await session.commit()

    @staticmethod
    @create_async_session
    async def get(event_id: int = None,
                  session: AsyncSession = None) -> EventInDBSchema | None:
        events = await session.execute(
            select(Event)
                .where(Event.id == event_id)
        )
        if event := events.first():
            return EventInDBSchema(**event[0].__dict__)

    @staticmethod
    @create_async_session
    async def get_all(session: AsyncSession = None) -> list[EventInDBSchema]:
        events = await session.execute(
            select(Event).order_by(Event.id)
        )
        return [EventInDBSchema(**event[0].__dict__) for event in events]

    @staticmethod
    @create_async_session
    async def update(event: EventInDBSchema, session: AsyncSession = None) -> None:
        await session.execute(
            update(Event)
            .where(Event.id == event.id)
            .values(**event.dict())
        )
        await session.commit()
