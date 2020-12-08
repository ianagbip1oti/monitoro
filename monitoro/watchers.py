import logging

import yaml


class Watchers:
    def __init__(self, file):
        self.file = file
        self.watchers = {}

        try:
            with open(file) as f:
                self.watchers = yaml.safe_load(f.read())
        except FileNotFoundError:
            logging.warn("Could not find previous monitoring data: %s", file)

    def add(self, bot_id, watcher_id, minutes=0):
        self.remove(bot_id, watcher_id)
        self.watchers.update(
            {
                bot_id: self.get_watchers(bot_id)
                + [{"watcher": watcher_id, "minutes": minutes}]
            }
        )
        self.save()

    def remove(self, bot_id, watcher_id):
        self.watchers.update(
            {
                bot_id: [
                    w for w in self.get_watchers(bot_id) if w["watcher"] != watcher_id
                ]
            }
        )
        self.save()

    def save(self):
        with open(self.file, "w") as f:
            yaml.dump(self.watchers, f)

    def is_watched(self, bot_id):
        return bot_id in self.watchers

    def get_watchers(self, bot_id):
        return self.watchers.get(bot_id, [])

    def get_watching(self, user_id):
        return (
            bot_id
            for bot_id in self.watchers
            if self.is_watching(bot_id=bot_id, user_id=user_id)
        )

    def is_watching(self, bot_id, user_id):
        return any(True for w in self.get_watchers(bot_id) if w["watcher"] == user_id)
