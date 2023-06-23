from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from config import CONFIG


class IsAdmin(BoundFilter):
    key = "is_admin"

    async def check(self, message: Message) -> bool:
        return message.from_user.id in CONFIG.BOT.ADMINS
