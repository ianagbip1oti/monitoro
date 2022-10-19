# Monitoro

[![Discord](https://img.shields.io/discord/417389758470422538)](https://discord.gg/3aTVQtz)

Discord bot that monitors the online status of other Discord bots.

## Usage

[Invite Monitoro](https://discord.com/api/oauth2/authorize?client_id=737425645771948123&permissions=0&scope=bot) to a server that also has the bot you wish to monitor.
Monitoro does not need to be present on all servers that your bot is,
but must share at least on server with your bot.

### Commands
Make sure that the bot has the permissions to view the message history of the channel where you are sending the commands!

```console
monitoro watch <bot id>
```

Watch the bot with the given id, receiving a DM when that bot goes offline.
This command must be issued in the server that has both Monitoro and the bot.

```console
monitoro status
```

View the online status of all bots that you are monitoring.

## Contact

Reach out for support, feedback, to contribute, or any other reason
at [Discord Projects Hub.](https://discord.gg/3aTVQtz)

## Credits

* Monitoro makes use of [smalld.py](https://github.com/princesslana/smalld.py) and
  [smalld-click](https://github.com/aymanizz/smalld-click)

* Icon made by [Freepik](http://www.freepik.com/) from [www.flaticon.com](https://www.flaticon.com)
