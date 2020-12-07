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
        self.on_offline_listeners = []

    def __getitem__(self, bot_id):
        return self.statuses.get(bot_id, Status.UNKNOWN)

    def update_from_presence(self, bot_id, presence):
        old = self[bot_id]
        new = Status.from_presence(presence)
        changed = new != old

        self.statuses[bot_id] = new

        if changed and new == Status.OFFLINE:
            for l in self.on_offline_listeners:
                l(bot_id)

    def add_listener(self, on_offline):
        self.on_offline_listeners.append(on_offline)
