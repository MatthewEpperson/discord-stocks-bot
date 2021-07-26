import io
import discord
import time
from datetime import *
import asyncio
import sys
import random
import os
from bs4 import BeautifulSoup
import requests
from discord.ext import commands
from datetime import datetime
import pyowm
import tweepy
import time
import json



token = ('')
client = commands.Bot('!')
daily_spin_date = {}
jahcoins = {}
client.jahcoins = {}
jahcoin_emoji = '<:jahcoin2:600180930761588747>'


@client.event
#This tells you that the bot is loaded and working
async def on_ready():
    print("Bot is loaded.")
    try:
        with open('jahcoins.json') as f:
            client.jahcoins = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        print("Couldn't load jahcoins.json, likely because file is empty")
        with open('jahcoins.json', 'w') as f:
            f.write("{}")
        client.jahcoins = {} 


@client.command(aliases = ['balance'])
async def bal(ctx):
    channel = ctx.message.channel
    id_ = str(ctx.message.author.id)
    if id_ in client.jahcoins:
        await ctx.send(f"You have {(client.jahcoins[id_]['coins'])}{jahcoin_emoji} {ctx.message.author.mention}")
        _save()
    elif id_ not in client.jahcoins:
        await ctx.send(f"You do not have an account, please make one by typing !register {ctx.message.author.mention}")


@client.command()
async def gamble(ctx, gamble_amount: int):
    channel = ctx.message.channel
    id_ = str(ctx.message.author.id)
    if id_ in client.jahcoins:
        random_number = random.randint(0,100)
        correct_number = random.randint(0,100)
        gamble_amount = int(ctx.message.content[8:])
        if gamble_amount > client.jahcoins[id_]["coins"]:
            await channel.send(f"You don't have enough! You have {(client.jahcoins[id_]['coins'])}{jahcoin_emoji} when you tried betting {gamble_amount}{jahcoin_emoji} {ctx.message.author.mention}")
        elif gamble_amount <= client.jahcoins[id_]["coins"]:
            if random_number < correct_number:
                client.jahcoins[id_]["coins"] += gamble_amount
                _save()
                await channel.send(f'You won! Congratulations, you now have {(client.jahcoins[id_]["coins"])}{jahcoin_emoji} {ctx.message.author.mention}')
            elif random_number > correct_number:
                client.jahcoins[id_]["coins"] -= gamble_amount
                _save()
                await channel.send(f'Unfortunately you lost, you now have {(client.jahcoins[id_]["coins"])}{jahcoin_emoji} {ctx.message.author.mention}')

@client.command()
@commands.cooldown(1, 60*60*24, commands.BucketType.user)
async def dailyspin(ctx):
    from collections import namedtuple
    results_template = namedtuple("result", ["percent", "amount", "message"])
    channel = ctx.message.channel
    id_ = str(ctx.message.author.id)
    if id_ in client.jahcoins:
        random_number = random.uniform(0.0, 100.0)
        await channel.send('You spin the wheel really fast. . .')
        await asyncio.sleep(0.75)
        await channel.send('The wheel continues to spin fast. . .')
        await asyncio.sleep(0.75)
        await channel.send('The wheel begins to slow down. . .')
        await asyncio.sleep(0.75)
        await channel.send('The wheel is just about to stop. . .')
        await asyncio.sleep(0.75)
        if random_number <= 5.0:
            result = results_template(5, 5000, "INCREDLBE LUCK!")
        elif random_number <= 10.0:
            result = results_template(10, 2500, "INSANE!")
        elif random_number <= 20.0:
            result = results_template(20, 1250, "Good job!")
        elif random_number <= 30.0:
            result = results_template(30, 800, "Not too shabby!")
        elif random_number <= 50.0:
            result = results_template(50, 500, "could have been better...")
        elif random_number <= 75.0:
            result = results_template(75, 250, "Not the worst...")
        elif random_number <= 100.0:
            result = results_template(100, 100, "the worst, better luck tomorrow!")
        client.jahcoins[id_]["coins"] += (result.amount)
        await ctx.send(f"The wheel finally stops and with a {result.percent}% chance, you won {result.amount}{jahcoin_emoji} for your daily spin,\n {result.message}!\n\nYour new balance is: {(client.jahcoins[id_]['coins'])}{jahcoin_emoji}{ctx.message.author.mention}")
        _save()
        

    if id_ not in client.jahcoins:
            await ctx.send(f"You don't have an account! Please type !register to make an account {ctx.message.author.mention}")
            return

@dailyspin.error
async def dailyspin_error(ctx, error):
    id_ = str(ctx.message.author.id)
    if isinstance(error, commands.CommandOnCooldown):
        #client.jahcoins[id_]["next_time"] = time.time() - next_time() > 246060
        await ctx.send(f"You already had your daily, your next spin will be in {round(error.retry_after / 60)} minutes")
    


@client.command()
async def register(ctx):
    id_ = str(ctx.message.author.id)
    channel = ctx.message.channel
    if id_ not in jahcoins:
        client.jahcoins[id_] = {"coins": 100, "next_time": 0}
        await channel.send(f"You are now registered and have been given 100{jahcoin_emoji} {ctx.message.author.mention}")
        _save()
    else:
        await channel.send(f"You already have an account {ctx.message.author.mention}")

@client.command()
async def give(ctx, other: discord.Member, jahcoin: int):
    channel = ctx.message.channel
    primary_id = str(ctx.message.author.id)
    other_id = str(other.id)
    if primary_id not in client.jahcoins:
        await ctx.send(f"You do not have an account, create one by typing !register {ctx.message.author.mention}")
    elif other_id not in client.jahcoins:
        await ctx.send(f"The other party {other.mention} does not have an account, he/or she needs to type !register {ctx.message.author.mention}")
    elif client.jahcoins[primary_id]['coins'] < jahcoin:
        await ctx.send(f"You cannot afford to give {other.mention} {jahcoin}{jahcoin_emoji} because you only have {(client.jahcoins[primary_id]['coins'])}{jahcoin_emoji} {ctx.message.author.mention}")
    else:
        client.jahcoins[primary_id]['coins'] -= jahcoin
        client.jahcoins[other_id]['coins'] += jahcoin
        await ctx.send(f"Transaction complete.\n\n{other.mention} new balance is: {(client.jahcoins[other_id]['coins'])}{jahcoin_emoji}\n\n{ctx.message.author.mention} new balance is: " +
                                  f"{(client.jahcoins[primary_id]['coins'])}{jahcoin_emoji}")
    _save()

@give.error
async def give_error(ctx, error):
    id_ = ctx.message.author.id
    if isinstance(error, commands.BadArgument):
        await ctx.send("**\nBAD INPUT**\n\nRemember !give @USER_NAME (amount)")



@client.command()
async def jahcoin(ctx):
    channel = ctx.message.channel
    embed = discord.Embed(title = "How to use Jahcoin Currency", color = 0xdaa520)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/593203992541003807/600183870520033281/exclamation.png")
    embed.add_field(name = "=== Registering ===", value = "First thing first is to register an account by typing **!register**.\nThis will register you into the database and start you out with 100 Jahcoin(s).", inline = True)
    embed.add_field(name = "=== Gambling ===", value = " You can gamble your jahcoin by typing **!gamble (amount to gamble)**. If you win, the amount you gambled will be added to your balance, if you lose the amount, you gambled will be taken away.", inline = True)
    embed.add_field(name = "=== Daily Spin ===", value = "You can have a daily spin by typing **!dailyspin**.", inline = True)
    embed.add_field(name = "=== Checking your Balance ===", value = "To check your balance simply type **!bal**.", inline = True)
    embed.add_field(name = "=== Giving ===", value = "Feeling generous? Give some of your {jahcoin_emoji} to another user by\ntyping **!give (amount) @USER**.", inline = True)
    embed.add_field(name = "=== Balance ===", value = "Checking your balance is simple, type either **!bal** or **!balance**.", inline = True)
    
    await channel.send(content=None, embed=embed)



def _save():
    with open('jahcoins.json', 'w') as f:
        json.dump(client.jahcoins, f)


@client.command()
async def cmds(ctx):
        embed = discord.Embed(title = "AwnBot Commands", color = 0x008000)
        embed.add_field(name = "!gm", value = "Says good morning & tells word of the day + Bible verse of the day + today's date\n" + "-"*95, inline = False)
        embed.add_field(name = "!8ball", value = "Let's you play 8-ball\n" + "-"*95, inline = False)
        embed.add_field(name = "!coinflip", value = "Flips a coin for heads or tails\n" + "-"*95, inline = False)
        embed.add_field(name = "!say", value = "Repeats whatever your \nmessage is in Text-to-speech\n" + "-"*95, inline = False)
        embed.add_field(name = "!weather", value = "Shows current temperature of a city by the following format: !weather (CITY NAME, COUNTRY CODE) with no parantheses.\n" + "-"*95, inline = False)
        embed.add_field(name = "!chance", value = "Gives you a random percentage between 0-100% of something happening.\n Example: !chance The Pats win the super bowl this year?\n" + "-"*95, inline = False)
        embed.add_field(name = "!kawhi", value = "WHAT IT DO BABY, check for yourself what it does ;)" + "-"*95 , inline = False)
        embed.add_field(name = "!randomvid", value = "Sends a random video, usually a funny meme", inline = False)
        embed.add_field(name = "!jahcoin", value = "Tells you the list of commands for our discord currency, Jahcoin.", inline = False)
           
        await ctx.send(content=None, embed=embed)

        

@client.command(name = "8ball")
async def _8ball(ctx):
        responses = ['It is certain.','It is decidedly so.','Without a doubt','Yes - definitely',
                        'You may rely on it.','As I see it, yes.','Most likely.','Outlook good.','Yes.',
                        'Signs point to yes.','Reply hazy, try again','Ask again later','Better not tell you now',
                        'Cannot predict now.','Concentrate and ask again','Do not count on it','My reply is no.',
                        'My sources say no.','Outlook not so good.','Very doubtful.']
        channel = message.channel
        
        await ctx.send(random.choice(responses) + f" {message.author.mention}")


        


@client.command()
async def coinflip(ctx):
        channel = ctx.message.channel
        await channel.send('Coin is tossed in the air . . .')
        time.sleep(1.5)
        await channel.send('Coin flips numerous times before landing . . .')
        time.sleep(1.5)
        await channel.send('The coin finally lands. . . and it is ' + random.choice(['Heads','Tails']) + f" {ctx.message.author.mention}")


@client.command()
async def say(ctx):
        channel = ctx.message.channel
        args = ctx.message.content.split(" ")
        await channel.send("%s" % (" ".join(args[1:])), tts=True)


@client.command()
async def gmall(ctx):
        channel = ctx.message.channel
        if ctx.message.author.id == '':
            await channel.send("Good morning Bobby Shmelter nation! <@>\n" + "Good morning Carbon nation! <@>\n"
                                        + "Good morning seb nation! <@>\n" + "Good morning Tazz Nation! <@>\n" + "Good morning ramsey nation! <@>")


@client.command()
async def gm(ctx):
        channel = ctx.message.channel
        date = datetime.today().strftime('%Y-%m-%d')
        bibledate = datetime.today().strftime('%Y/%m/%d')

        await channel.send(f"Good morning! {ctx.message.author.mention}\n" + "\nToday's date is " + date + " \n\n**Below is the word of the day**\n" + "https://www.merriam-webster.com/word-of-the-day\n")
        await channel.send("\n**Bible verse of the day is below**" + "\nhttps://www.dailyverses.net/" + bibledate)


@client.command()
async def weather(ctx):
        channel = ctx.message.channel
        degree_sign = u'\N{DEGREE SIGN}'
        owm = pyowm.OWM('')
        location = ctx.message.content[9:]
        zipcode = ctx.message.content[9:]
        observation = owm.weather_at_place(location or zipcode)
        weather = observation.get_weather()
        temperature = weather.get_temperature('fahrenheit')['temp']
        wind = weather.get_wind('miles_hour')['speed']
        windspeed = (round(wind, 2))
        humidity = weather.get_humidity()
        status = weather.get_detailed_status()

        embed = discord.Embed(title = f'Weather for {location}', color = 0x00ffff)
        embed.add_field(name = "-"*99, value = f':thermometer: The temperature in {location} is {temperature}{degree_sign}F', inline = False)
        embed.add_field(name = "-"*99, value = f':dash: {location} has a wind speed of {windspeed} mph.', inline = False)
        embed.add_field(name = "-"*99, value = f':sweat_drops: {location} humidity is {humidity}% with {status}', inline = False)

        await channel.send(content=None, embed=embed)



@client.command()
async def chance(ctx):
        channel = ctx.message.channel
        percentage = (random.uniform(0.00, 100.00))
        percent = (round(percentage, 2))
        
        await channel.send(f'There is a {percent}% chance of it happening. {ctx.message.author.mention}')
        
@client.command()
async def kawhi(ctx):
    channel = ctx.message.channel
    await channel.send("WHAT IT DO BABY", file = discord.File(r"C:\Users\Matt\Desktop\AwnBot Discord\kawhi.mp4"))


@client.command()
async def randomvid(ctx):
    path ='C:/Users/Matt/Desktop/AwnBot Discord/meme vids'
    files = os.listdir(path)
    index = random.randrange(0, len(files))
    vidName = (files[index])

    await ctx.send(file = discord.File(r'C:/Users/Matt/Desktop/AwnBot Discord/meme vids/' + vidName))
                                               
client.run(token)
                            


            
      
