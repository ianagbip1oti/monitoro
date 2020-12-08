from enum import Enum, auto


class Status(Enum):
    OFFLINE = auto()
    ONLINE = auto()
    UNKNOWN = auto()

    @staticmethod
    def from_presence(presence):
        if presence in {"online", "idle", "dnd"}:
            return Status.ONLINE
        elif presence in {"offline"}:
            return Status.OFFLINE

        return Status.UNKNOWN


class Statuses:
    def __init__(self):
        self.statuses = {}
        self.listeners = []

    def __getitem__(self, bot_id):
        return self.statuses.get(bot_id, Status.UNKNOWN)

    def update_from_presence(self, bot_id, presence):
        old = self[bot_id]
        new = Status.from_presence(presence)

        self.statuses[bot_id] = new

        if new != old:
            for l in (l for s, l in self.listeners if s == new):
                l(bot_id)

    def add_listener(self, on_offline=None, on_online=None):
        if on_offline:
            self.listeners.append((Status.OFFLINE, on_offline))

        if on_online:
            self.listeners.append((Status.ONLINE, on_online))
