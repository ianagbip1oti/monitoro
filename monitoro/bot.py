from smalld import SmallD, Intent
from smalld_click import SmallDCliRunner, get_conversation
import logging
import yaml
import os
from dataclasses import dataclass
import click

logging.basicConfig(level=logging.INFO)


statuses = {}
monitoring = {}


@click.group()
def monitoro():
    pass


@monitoro.command()
@click.argument("bot_id", nargs=1)
def watch(bot_id):
    watcher_id = get_conversation().user_id

    dm_channel = smalld.post("/users/@me/channels", {"recipient_id": watcher_id})

    monitoring.update(
        {bot_id: monitoring.get(bot_id, []) + [(watcher_id, dm_channel.id)]}
    )

    smalld.post(
        f"/channels/{dm_channel.id}/messages",
        {"content": f"You are now watching {bot_id}"},
    )

    click.echo(f"You are now watching {bot_id}")


smalld = SmallD(
    intents=Intent.GUILD_MESSAGES | Intent.DIRECT_MESSAGES | Intent.GUILD_PRESENCES
)


@smalld.on_presence_update
def on_presence_update(update):
    monitored = update.user.id
    monitored_by = monitoring.get(monitored, [])
    previous_status = statuses.get(monitored, None)

    if monitored_by and update.status != previous_status:
        statuses[monitored] = update.status

        if update.status == "offline":
            for user, channel in monitored_by:
                smalld.post(
                    f"/channels/{channel}/messages",
                    {"content": f"{update.user.id} went {update.status}"},
                )


def run():
    with SmallDCliRunner(smalld, monitoro, prefix=""):
        smalld.run()
