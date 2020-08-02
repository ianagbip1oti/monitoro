from smalld import SmallD, Intent
from smalld_click import SmallDCliRunner, get_conversation
import logging
import yaml
import os
from dataclasses import dataclass
import click
import monitoro.discord as discord

logging.basicConfig(level=logging.INFO)

DATA_DIR = os.environ.get("MT_DATA", "data")
MONITORING_FILE = os.path.join(DATA_DIR, "monitoring.yaml")

statuses = {}
monitoring = {}

try:
    with open(MONITORING_FILE) as f:
        monitoring = yaml.safe_load(f.read())
except FileNotFoundError:
    logging.warn("Could not find previous monitoring data: %s", MONITORING_FILE)


@click.group()
def monitoro():
    pass


@monitoro.command()
@click.argument("bot_id", nargs=1)
def watch(bot_id):
    watcher_id = get_conversation().user_id

    monitoring.update({bot_id: monitoring.get(bot_id, []) + [{"watcher": watcher_id}]})

    with open(MONITORING_FILE, "w") as f:
        yaml.dump(monitoring, f)

    watching = discord.get_user(smalld, bot_id)

    if not watching.get("bot", False):
        click.echo(f"{bot_id} is not a bot")
        click.get_current_context().abort()

    confirmation = f"You are now watching **{watching.username}**"
    dm_channel = discord.get_dm_channel(smalld, watcher_id)

    smalld.post(
        f"/channels/{dm_channel.id}/messages", {"content": confirmation},
    )

    click.echo(confirmation)


smalld = SmallD(
    intents=Intent.GUILD_MESSAGES | Intent.DIRECT_MESSAGES | Intent.GUILD_PRESENCES
)


@smalld.on_presence_update
def on_presence_update(update):
    monitored_id = update.user.id
    monitored_by = monitoring.get(monitored_id, [])
    previous_status = statuses.get(monitored_id, None)

    if monitored_by and update.status != previous_status:
        statuses[monitored_id] = update.status

        if update.status == "offline":
            watching = discord.get_user(smalld, monitored_id)

            for user in monitored_by:
                dm_channel = discord.get_dm_channel(smalld, user["watcher"])

                smalld.post(
                    f"/channels/{dm_channel.id}/messages",
                    {"content": f"**{watching.username}** went {update.status}"},
                )


def run():
    name = os.environ.get("MT_NAME", "monitoro")

    with SmallDCliRunner(smalld, monitoro, prefix="", name=name):
        smalld.run()
