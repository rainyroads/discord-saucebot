# SauceBot
[![GitHub](https://img.shields.io/github/license/rainyDayDevs/discord-saucebot)](https://github.com/rainyDayDevs/discord-saucebot/blob/master/LICENSE.md)

SauceBot is an open-source Discord bot built on the [Hikari](https://github.com/hikari-py/hikari) framework that utilizes the [SauceNao API](https://saucenao.com/) to find the source of images or anime screencaps.

## Documentation
### Inviting the bot
You can invite SauceBot to your server using the following invite link:

https://discord.com/api/oauth2/authorize?client_id=718642000898818048&permissions=414464657472&scope=bot%20applications.commands

### Using the bot
The primary way to use SauceBot is through message commands.

Simply right-click a message that contains an image you want to look up, then go to apps, and click the "sauce" option.

The bot also supports slash commands, which you to look up the source of images via attachment uploads or image URL's.
```
/sauce file
/sauce url https://i.redd.it/rqtzjynwx7351.jpg
```

![Bot demonstration](https://github.com/rainyDayDevs/discord-saucebot/assets/7929996/803ebe3c-b253-4d17-b757-fdb27c02b2f5)


### Increasing your API limits
Each Discord server is currently allotted 100 free API queries/day from a shared pool.

If you run a larger server and need more API queries, you can upgrade to a limit of 5,000 queries/day by obtaining an [enhanced license key](https://saucenao.com/user.php?page=account-upgrades) directly from SauceNao for $6/month.

To register an API key to your server, run the `/config api_key` command under an administrator account.

You should receive a confirmation message afterwards verifying your API key was successfully linked.

Keep in mind, this will only work for **enhanced** license keys. Freely registered API keys will not work, as these are still IP restricted (meaning, multiple free accounts cannot be used on the same network). If you want to use a freely registered API key, you'll need to run your own instance of the bot.

### Patreons

Thank you so much to all of our supporters on [Patreon](https://www.patreon.com/saucebot)! It means a lot to me that you
believe in this project enough to help fund it.

A full list of our active and previous Patrons can be found in the [PATRONS.md](./PATRONS.md) file.

#### Active Patron's ($6)

- Alexis
- Nali
- Heber 
- JanJan 
- SUZUSHIIRO
- Defolota 
- zhimin huang
- Elroid 
- Justin Whang
- Ty Newman
