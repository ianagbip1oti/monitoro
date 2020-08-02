import logging
import os

import click
from smalld import Intent, SmallD
from smalld_click import SmallDCliRunner, get_conversation

import monitoro.discord as discord
from monitoro.watchers import Watchers

logging.basicConfig(level=logging.INFO)

DATA_DIR = os.environ.get("MT_DATA", "data")
MONITORING_FILE = os.path.join(DATA_DIR, "monitoring.yaml")

statuses = {}
watchers = Watchers(MONITORING_FILE)

STATUS_ICON_UNKNOWN = "❓"
STATUS_ICONS = {
    "online": "✅",
    "idle": "✅",
    "dnd": "✅",
    "offline": "❌",
}


@click.group()
def monitoro():
    pass


@monitoro.command()
@click.argument("bot_id", nargs=1)
def watch(bot_id):
    watching = discord.get_user(smalld, bot_id)

    if not watching.get("bot", False):
        click.echo(f"{bot_id} is not a bot")
        click.get_current_context().abort()

    watcher_id = get_conversation().user_id
    watchers.add(bot_id=bot_id, watcher_id=watcher_id)

    confirmation = f"You are now watching **{watching.username}**"
    dm_channel = discord.get_dm_channel(smalld, watcher_id)

    smalld.post(
        f"/channels/{dm_channel.id}/messages", {"content": confirmation},
    )

    if guild_id := get_conversation().message.get("guild_id"):
        smalld.send_gateway_payload(
            {
                "op": 8,
                "d": {
                    "guild_id": guild_id,
                    "limit": 1,
                    "presences": True,
                    "user_ids": bot_id,
                },
            }
        )

    click.echo(confirmation)


@monitoro.command()
def status():
    watcher_id = get_conversation().user_id

    for bot in (
        discord.get_user(smalld, bot_id) for bot_id in watchers.get_watching(watcher_id)
    ):
        icon = STATUS_ICONS.get(statuses.get(bot.id), STATUS_ICON_UNKNOWN)

        click.echo(f"{icon} {bot.username}")


smalld = SmallD(
    intents=Intent.GUILDS
    | Intent.GUILD_MESSAGES
    | Intent.DIRECT_MESSAGES
    | Intent.GUILD_PRESENCES
)


@smalld.on_presence_update
def on_presence_update(update):
    monitored_id = update.user.id
    monitored_by = watchers.get_watchers(monitored_id)
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


@smalld.on_guild_create
@smalld.on_guild_members_chunk
def on_guild_create(create):
    bot_ids = {m.user.id for m in create.get("members", []) if m.user.get("bot", False)}

    for update in create.get("presences", []):
        if update.user.id in bot_ids or watchers.is_watched(update.user.id):
            statuses[update.user.id] = update.status


def run():
    name = os.environ.get("MT_NAME", "monitoro")

    with SmallDCliRunner(smalld, monitoro, prefix="", name=name):
        smalld.run()
