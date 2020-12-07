import sched
from threading import Thread

import monitoro.discord as discord


class Notifications:
    def __init__(self, smalld, watchers):
        self.smalld = smalld
        self.watchers = watchers

    def notify_offline(self, bot_id):
        monitored_by = self.watchers.get_watchers(bot_id)

        if monitored_by:
            watching = discord.get_user(self.smalld, bot_id)

            def send_dm():
                dm_channel = discord.get_dm_channel(self.smalld, user["watcher"])

                self.smalld.post(
                    f"/channels/{dm_channel.id}/messages",
                    {"content": f"**{watching.username}** went offline"},
                )

            scheduler = sched.scheduler()

            for user in monitored_by:
                scheduler.enter(0, 0, send_dm)

            Thread(target=scheduler.run).start()
