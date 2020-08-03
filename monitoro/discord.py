import functools
from smalld import HttpError


@functools.lru_cache
def get_user(smalld, user_id):
    return smalld.get(f"/users/{user_id}")


@functools.lru_cache
def get_guild_member(smalld, guild_id, user_id):
    try:
        return smalld.get(f"/guilds/{guild_id}/members/{user_id}")
    except HttpError as e:
        if e.response.status_code == 404:
            return None
        else:
            raise


@functools.lru_cache
def get_dm_channel(smalld, user_id):
    return smalld.post("/users/@me/channels", {"recipient_id": user_id})
