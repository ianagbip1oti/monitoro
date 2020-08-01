import functools


@functools.lru_cache
def get_user(smalld, user_id):
    return smalld.get(f"/users/{user_id}")
