import functools


@functools.lru_cache
def get_user(smalld, user_id):
    return smalld.get(f"/users/{user_id}")


@functools.lru_cache
def get_dm_channel(smalld, user_id):
    return smalld.post("/users/@me/channels", {"recipient_id": user_id})
