from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import UserSchema, UserInDBSchema
from models import User, create_async_session


class CRUDUser(object):

    @staticmethod
    @create_async_session
    async def add(user: UserSchema, session: AsyncSession = None) -> UserInDBSchema | None:
        user = User(**user.dict())
        session.add(user)
        try:
            await session.commit()
        except IntegrityError as eq:
            print(eq)
        else:
            await session.refresh(user)
            return UserInDBSchema(**user.__dict__)

    @staticmethod
    @create_async_session
    async def delete(user_id: int, session: AsyncSession = None) -> None:
        await session.execute(
            delete(User)
            .where(User.id == user_id)
        )
        await session.commit()

    @staticmethod
    @create_async_session
    async def get(user_id: int = None, db_id: int = None, session: AsyncSession = None) -> UserInDBSchema | None:
        if user_id:
            user = await session.execute(
                select(User)
                .where(User.user_id == user_id)
            )
        else:
            user = await session.execute(
                select(User)
                .where(User.id == db_id)
            )
        if user := user.first():
            return UserInDBSchema(**user[0].__dict__)

    @staticmethod
    @create_async_session
    async def get_all(session: AsyncSession = None) -> list[UserInDBSchema]:
        users = await session.execute(
            select(User)
        )
        return [UserInDBSchema(**user[0].__dict__) for user in users]

    @staticmethod
    @create_async_session
    async def update(user_id: UserInDBSchema, session: AsyncSession = None) -> None:
        await session.execute(
            update(User)
            .where(User.id == user_id.id)
            .values(**user_id.dict())
        )
        await session.commit()
