import logging
import os
from datetime import datetime

import click
import humanize
from pkg_resources import get_distribution
from smalld import Intent, SmallD
from smalld import __version__ as smalld_version
from smalld_click import SmallDCliRunner
from smalld_click import __version__ as smalld_click_version
from smalld_click import get_conversation

import monitoro.discord as discord
from monitoro.notifications import Notifications
from monitoro.status import Status, Statuses
from monitoro.watchers import Watchers

NAME = os.environ.get("MT_NAME", "monitoro")
DATA_DIR = os.environ.get("MT_DATA", "data")
MONITORING_FILE = os.path.join(DATA_DIR, "monitoring.yaml")

logging.basicConfig(level=logging.DEBUG if os.environ.get("MT_DEBUG") else logging.INFO)
logger = logging.getLogger("monitoro.bot")

start_time = datetime.now()

smalld = SmallD(
    intents=Intent.GUILDS
    | Intent.GUILD_MESSAGES
    | Intent.DIRECT_MESSAGES
    | Intent.GUILD_PRESENCES
)

statuses = Statuses()
watchers = Watchers(MONITORING_FILE)
notifications = Notifications(smalld, watchers)

statuses.add_listener(
    on_offline=notifications.notify_offline, on_online=notifications.on_online
)

STATUS_ICONS = {
    Status.UNKNOWN: "❓",
    Status.ONLINE: "✅",
    Status.OFFLINE: "❌",
}


@click.group()
def monitoro():
    """
    Monitoro is a bot to monitor the online status of Discord bots.

    Watching a bot means that you will receive a DM when Monitoro
    detects that bot is offline.

    \b
    To get started watching a bot issue a watch command. For example:
      monitoro watch 737425645771948123
    """


@monitoro.command()
@click.option(
    "--minutes",
    default=0,
    help="Minutes to wait before alerting",
    type=int,
    show_default=True,
)
@click.argument("bot_id", nargs=1)
def watch(bot_id, minutes):
    """
    Watch the online status of a bot.

    If the watched bot goes offline you will be sent a DM informing you.
    Providing the minutes parameter will mean a DM is only sent if the
    watched bot has been offline for at least that number of minutes.

    This command must be issued in a guild that has both Monitoro and
    the bot to be watched as members.

    \b
    Examples:
      monitoro watch 737425645771948123
      monitoro watch --minutes 5 737425645771948123
    """

    guild_id = get_conversation().message.get("guild_id")

    if not guild_id:
        click.echo(f"This command must be issued in a guild")
        click.get_current_context().abort()

    watching = discord.get_guild_member(smalld, guild_id, bot_id)

    if not watching or not watching.user.get("bot", False):
        click.echo(f"{bot_id} is not a bot in this guild")
        click.get_current_context().abort()

    watcher_id = get_conversation().user_id
    watchers.add(bot_id=bot_id, watcher_id=watcher_id, minutes=minutes)

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

    click.echo(
        f"You are now watching **{watching.user.username}** (<@!{watching.user.id}>)"
    )


@monitoro.command()
@click.argument("bot_id", nargs=1)
def unwatch(bot_id):
    """
    Stop watching the online status of a bot.

    \b
    Example:
      monitoro unwatch 737425645771948123
    """

    watching = discord.get_user(smalld, bot_id)

    watcher_id = get_conversation().user_id
    watchers.remove(bot_id=bot_id, watcher_id=watcher_id)

    who = f"**{watching.username}**" if watching.get("bot", False) else bot_id

    click.echo(f"You have stopped watching {who}")


@monitoro.command()
def status():
    """
    Display the status of all bots you are watching.

    The status may be online (green checkmark), offline (red cross), or
    unknown (question mark).
    A bot's status being unknown means that Monitoro has not seen any
    presence change event for that bot yet.

    \b
    Example:
      monitoro status
    """

    watcher_id = get_conversation().user_id

    for bot in sorted(
        (
            discord.get_user(smalld, bot_id)
            for bot_id in watchers.get_watching(watcher_id)
        ),
        key=lambda b: b.username.lower(),
    ):
        icon = STATUS_ICONS[statuses[bot.id]]
        click.echo(f"{icon} {bot.username} ({bot.id})")


@monitoro.command()
def about():
    """
    Display information and stats about Monitoro.

    \b
    Example:
      monitoro about
    """

    channel_id = get_conversation().channel_id

    pkg = get_distribution("monitoro")

    bots, users = watchers.get_counts()
    stats_line = f"Watching **{bots} bots** for **{users} users**."
    uptime = humanize.precisedelta(
        datetime.now() - start_time, format="%.0f", minimum_unit="minutes"
    )

    def github_link(org, repo, name=None):
        return f"[{name or repo}](https://github.com/{org}/{repo})"

    stack = {
        ("ianagbip1oti", "monitoro"): pkg.version,
        ("aymanizz", "smalld-click"): smalld_click_version,
        ("princesslana", "smalld"): smalld_version,
    }

    stack_info = "\n".join(
        f"{github_link(*repo)}: {version}" for repo, version in stack.items()
    )

    smalld.post(
        f"/channels/{channel_id}/messages",
        {
            "embed": {
                "title": "Monitoro",
                "description": "Discord bot for monitoring the online status of Discord bots",
                "thumbnail": {
                    "url": (
                        "https://raw.githubusercontent.com/"
                        "ianagbip1oti/monitoro/master/avatar.png"
                    )
                },
                "fields": [
                    {"name": "Stats", "value": stats_line},
                    {"name": "Prefix", "value": NAME, "inline": True},
                    {
                        "name": "Links",
                        "value": "\n".join(
                            (
                                github_link(
                                    "ianagbip1oti", "monitoro", name="Source on GitHub"
                                ),
                                "[Discord Bot List](https://top.gg/bot/737425645771948123)",
                            )
                        ),
                        "inline": True,
                    },
                    {"name": "Uptime", "value": uptime, "inline": True},
                    {"name": "Stack", "value": stack_info},
                    {
                        "name": "Icon",
                        "value": (
                            "Made by [Freepik](http://www.freepik.com/) "
                            "from [www.flaticon.com](https://www.flaticon.com)"
                        ),
                    },
                ],
            }
        },
    )


@smalld.on_presence_update
def on_presence_update(update):
    statuses.update_from_presence(update.user.id, update.status)


@smalld.on_guild_create
@smalld.on_guild_members_chunk
def on_guild_create(create):
    bot_ids = {m.user.id for m in create.get("members", []) if m.user.get("bot", False)}

    for update in create.get("presences", []):
        if update.user.id in bot_ids or watchers.is_watched(update.user.id):
            statuses.update_from_presence(update.user.id, update.status)


def run():
    with SmallDCliRunner(smalld, monitoro, prefix="", name=NAME):
        smalld.run()
