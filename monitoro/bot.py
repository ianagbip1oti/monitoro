import logging
import os

import click
from smalld import Intent, SmallD
from smalld_click import SmallDCliRunner, get_conversation

import monitoro.discord as discord
from monitoro.status import Status, Statuses
from monitoro.watchers import Watchers

logging.basicConfig(level=logging.INFO)

DATA_DIR = os.environ.get("MT_DATA", "data")
MONITORING_FILE = os.path.join(DATA_DIR, "monitoring.yaml")

statuses = Statuses()
watchers = Watchers(MONITORING_FILE)

STATUS_ICONS = {
    Status.UNKNOWN: "❓",
    Status.ONLINE: "✅",
    Status.OFFLINE: "❌",
}


@click.group()
def monitoro():
    pass


@monitoro.command()
@click.argument("bot_id", nargs=1)
def watch(bot_id):
    guild_id = get_conversation().message.get("guild_id")

    if not guild_id:
        click.echo(f"This command must be issued in a guild")
        click.get_current_context().abort()

    watching = discord.get_guild_member(smalld, guild_id, bot_id)

    if not watching or not watching.user.get("bot", False):
        click.echo(f"{bot_id} is not a bot in this guild")
        click.get_current_context().abort()

    watcher_id = get_conversation().user_id
    watchers.add(bot_id=bot_id, watcher_id=watcher_id)

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

    click.echo(f"You are now watching **{watching.user.username}**")


@monitoro.command()
@click.argument("bot_id", nargs=1)
def unwatch(bot_id):
    watching = discord.get_user(smalld, bot_id)

    watcher_id = get_conversation().user_id
    watchers.remove(bot_id=bot_id, watcher_id=watcher_id)

    who = f"**{watching.username}**" if watching.get("bot", False) else bot_id

    click.echo(f"You have stopped watching {who}")


@monitoro.command()
def status():
    watcher_id = get_conversation().user_id

    for bot in (
        discord.get_user(smalld, bot_id) for bot_id in watchers.get_watching(watcher_id)
    ):
        icon = STATUS_ICONS[statuses[bot.id]]
        click.echo(f"{icon} {bot.username}")


smalld = SmallD(
    intents=Intent.GUILDS
    | Intent.GUILD_MESSAGES
    | Intent.DIRECT_MESSAGES
    | Intent.GUILD_PRESENCES
)


@smalld.on_presence_update
def on_presence_update(update):
    statuses.update_from_presence(update.user.id, update.status)


def notify_on_offline(bot_id):
    monitored_by = watchers.get_watchers(bot_id)

    if monitored_by:
        watching = discord.get_user(smalld, bot_id)

        for user in monitored_by:
            dm_channel = discord.get_dm_channel(smalld, user["watcher"])

            smalld.post(
                f"/channels/{dm_channel.id}/messages",
                {"content": f"**{watching.username}** went offline"},
            )


statuses.add_listener(on_offline=notify_on_offline)


@smalld.on_guild_create
@smalld.on_guild_members_chunk
def on_guild_create(create):
    bot_ids = {m.user.id for m in create.get("members", []) if m.user.get("bot", False)}

    for update in create.get("presences", []):
        if update.user.id in bot_ids or watchers.is_watched(update.user.id):
            statuses.update_from_presence(update.user.id, update.status)


def run():
    name = os.environ.get("MT_NAME", "monitoro")

    with SmallDCliRunner(smalld, monitoro, prefix="", name=name):
        smalld.run()
