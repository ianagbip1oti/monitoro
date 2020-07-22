from smalld import SmallD, Intent
import logging
import yaml
import os
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)


class Config:
    def __init__(self, yaml):
        self.yaml = yaml

    @property
    def notification_channel(self):
        return self.yaml["notification_channel"]

    def find_monitored(self, user_id):
        return next(
            (
                name
                for name, cfg in self.yaml["monitor"].items()
                if str(cfg["id"]) == user_id
            ),
            None,
        )

    def find_user_id(self, user_name):
        return self.yaml["users"][user_name]

    def find_pings(self, name):
        monitored = self.yaml["monitor"][name]

        return (self.find_user_id(n) for n in monitored.get("notify", []))


with open(os.environ.get("MT_CONFIG", "config.yaml")) as f:
    CONFIG = Config(yaml.safe_load(f.read()))


smalld = SmallD(intents=Intent.GUILD_PRESENCES)

statuses = {}


@smalld.on_presence_update
def on_presence_update(update):
    monitored = CONFIG.find_monitored(update.user.id)
    previous_status = statuses.get(monitored, None)

    if monitored and update.status != previous_status:
        statuses[monitored] = update.status

        pings = ""
        if update.status == "offline":
            pings = " ".join(
                f"<@{user_id}>" for user_id in CONFIG.find_pings(monitored)
            )

        smalld.post(
            f"/channels/{CONFIG.notification_channel}/messages",
            {"content": f"{monitored} went {update.status} {pings}"},
        )


smalld.run()
