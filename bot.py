import json
import time
import urllib.request
import discord

client = discord.Client()

# Dictionary that keep the previous cryptos prices to
# calculate the improvement in percents between the live price and the previous one
oldPrices = {'isFirstLoop': True}

# Get discord token from ./key/discord_token.key
# discord_token.key must only contain your token
with open('keys/discord_token.key') as file:
    TOKEN = file.read()

# Get bot settings => ./settings/bot_settings.json
with open('settings/settings.json') as file:
    settings   = json.load(file)
    channel_id = settings['channel_id']
    interval   = settings['interval'] 

    # If value of the 'channel_id' or 'interval' key is string, try to convert it to int
    # if can't convert => raise InvalidType error
    if isinstance(channel_id, str) or isinstance(interval, str):
        try:
            channel_id = int(channel_id)
            interval   = int(interval)
        except ValueError:
            raise InvalidType("Invalid channel id or interval, please use int")


# Called when discord bot is up
@client.event
async def on_ready():

    # change the discord status with values in ./settings/settings.json
    await client.change_presence(
        activity=discord.Activity(
            type=get_status(settings['status_type'])[0],
            name=get_status(settings['status_type'])[1]
        )
    )

    # Repeat every (interval)min while bot is up => send prices to the channel choosed
    while True:
        channel = client.get_channel(channel_id)
        await channel.send(embed=symbols_to_embed(return_symbols()))
        time.sleep(interval * 60)


# Return status & status type from bot_settings.json
def get_status(type):
    if 'playing' in type.lower():
        return [discord.ActivityType.playing, settings['status']]
    elif 'streaming' in type.lower():
        return [discord.ActivityType.streaming, settings['status']]
    elif 'listening' in type.lower():
        return [discord.ActivityType.listening, settings['status']]
    elif 'watching' in type.lower():
        return [discord.ActivityType.watching, settings['status']]
    else:
        raise UnknowStatusType("Status type must be: playing/streaming/listening/watching")


# Get and return symbols from ./settings/tokens.json 
# return format => [['crypto1', 'crypto2'], ['crypto3', 'crypto4']] => with crypto1+crypto2 = symbol (ex: 'BTCUSDT')
def return_symbols():
    i = []
    with open('settings/tokens.json') as tokenList:
        tokens = json.load(tokenList)
    # if tokens.json is not empty return a list to the correct format
    if len(tokens) > 0:
        for x in tokens:
            i.append([x, tokens[x]])
    # if tokens.json is empty, fill the list to return with default values ('BTCUSDT')
    else:
        i.append(['BTC', 'USDT'])
    return i


# Return the discord embed text with prices from list of symbols
def symbols_to_embed(symbolsList):
    prices = []

    # For each symbols in list of symbols, get live price
    for x in symbolsList:
        prices.append([(str(x[0]) + str(x[1])).upper(), return_prices(str(x[0]), str(x[1]))[1]])

    if oldPrices['isFirstLoop']:
        oldPrices['isFirstLoop'] = False
        for x in prices:
            oldPrices[str(x[0])] = str(x[1])

    t = time.localtime()
    current_time = time.strftime("%D %H:%M:%S", t)

    embed = discord.Embed(title="Prices ~ [m" + str(interval) + "]",
                          description=current_time, color=0xFF8008)
    embed.set_author(name="SatoshiNakamoto",
                     icon_url='https://cdn.discordapp.com/avatars/923323366197301278/8cc23d15abd47fbc1e0b7dc95dae2c38.webp?size=80')

    # For each cryptos prices in pricesList create field in the embed message
    for x in prices:
        embed.add_field(name=str(x[0]),
                        value='$' + str(x[1]) + ' ~ ' + '[' + get_improvement(oldPrices[x[0]], x[1]) + ']')
        oldPrices[str(x[0])] = str(x[1])
    return embed


# Return a list with prices based on the 2 crypto symbols in parameters
def return_prices(crypt1, crypt2):
    try:
        with urllib.request.urlopen(
                'https://www.binance.com/api/v3/ticker/price?symbol=' + crypt1.upper() + crypt2.upper()) as url:
            data = json.loads(url.read().decode())
        # list format: [Symbol , price]
        return [data[list(data)[0]], format(float(data[list(data)[1]]), ".2f")]
    except urllib.error.HTTPError:
        raise InvalidType("Invalid crypto or invalid symbols in ./settings/tokens.json")


# Return improvement in percents between two prices
def get_improvement(old, new):
    old = float(old)
    new = float(new)
    i = ((new - old) / old) * 100.0
    i = format(i, ".2f")
    if new >= old:
        return '+' + str(i) + '%'
    else:
        return str(i) + '%'


# Raised error if incorrect status type in settings
class UnknowStatusType(Exception):
    def __init__(self, error):
        super().__init__(error)

# Raised error if invalid type is given (=> channel_id ; interval or invalid cryptos symbols) 
class InvalidType(Exception):
    def __init__(self, error):
        super().__init__(error)


client.run(TOKEN)
