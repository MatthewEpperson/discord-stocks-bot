import discord
from discord.ext import commands
import time
import asyncio
import json
import os.path
import datetime as dt
from StockScraper import *
import sqlite3
import math
from disputils import BotEmbedPaginator, BotConfirmation, BotMultipleChoice

conn = sqlite3.connect('user_stock_history.db')

c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS BuyHistory (
            User text,
            Day text,
            Hour text,
            Stock text,
            BuyAmount int,
            BuyPrice real
            )""")

c.execute("""CREATE TABLE IF NOT EXISTS SellHistory (
            User text,
            Day text,
            Hour text,
            Stock text,
            SellAmount int,
            SellPrice real
            )""")


class stocks(commands.Cog):
    
    def __init__(self, client):
        self.client = client
        
    def save_file_coins(self):
        with open('jahcoins.json', 'w') as f:
            json.dump(self.client.jahcoins, f, indent = 4)

    def save_file_stocks(self):
        with open('userStocks.json', 'w') as f:
            json.dump(self.client.userStocks, f, indent = 4)

    def get_StockProfit(self, id_: str, stock_name):
        c.execute("SELECT SellAmount FROM SellHistory WHERE User=:id_ AND Stock=:stock_name ORDER BY Hour DESC LIMIT 1",
            {'id_': id_, 'stock_name': stock_name})
        boughtTotal = c.fetchone()[0]
        
        c.execute("SELECT PricePerShare FROM BuyHistory WHERE User=:id_ AND Stock=:stock_name ORDER BY Hour DESC LIMIT 1",
            {'id_': id_, 'stock_name': stock_name})
        priceOfShare = c.fetchone()[0]
        boughtTotal = boughtTotal * priceOfShare

        c.execute("SELECT SellPrice FROM SellHistory WHERE User=:id_ AND Stock=:stock_name ORDER BY Hour DESC LIMIT 1",
            {'id_': id_, 'stock_name': stock_name})
        sellTotal = c.fetchone()[0]

        profitTotal = sellTotal - boughtTotal
        profitPercent = (profitTotal / boughtTotal) * 100

        return profitTotal, profitPercent

    def get_StockSellHistory(self, id_: str):
        c.execute("SELECT * FROM SellHistory WHERE User=:id_", {'id_': id_})
        return c.fetchall()

    def insert_StockBuyHistory(self, id_: str, day: str, hour: str, stock_name: str, buyAmount: int, buyPrice: float, PricePerShare: float):
        with conn:
            c.execute("INSERT INTO BuyHistory VALUES (:User, :Day, :Hour, :Stock, :BuyAmount, :BuyPrice, :PricePerShare)",
                {'User': id_, 'Day': day, 'Hour': hour, 'Stock': stock_name, 'BuyAmount': buyAmount, 'BuyPrice': buyPrice, "PricePerShare": PricePerShare})

    def get_StockBuyHistory(self, id_: str):
        c.execute("SELECT * FROM BuyHistory WHERE User=:id_", {'id_': id_})
        return c.fetchall()

    def insert_StockSellHistory(self, id_: str, day: str, hour: str, stock_name: str, sellAmount: int, sellPrice: float):
        with conn:
            c.execute("INSERT INTO SellHistory VALUES (:User, :Day, :Hour, :Stock, :SellAmount, :SellPrice)",
                {'User': id_, 'Day': day, 'Hour': hour, 'Stock': stock_name, 'SellAmount': sellAmount, 'SellPrice': sellPrice})


    @commands.command()
    async def stock(self, ctx, stock_name: str):
        channel = ctx.message.channel
        id_ = str(ctx.message.author.id)
        stockImage = stockGraph(stock_name)
        file = discord.File(f"C:/Users/Matt/Desktop/AwnBot Discord/Stock Screenshots/{stock_name}.png", filename="image.png")
        embed = discord.Embed(title = f"${stock_name.upper()} | Current Price: ${GetStockPrice(stock_name)}", color = 0xdaa520)
        embed.set_image(url="attachment://image.png")
        return await ctx.send(file=file, embed=embed)

    @commands.command()
    async def mystocks(self, ctx, stock_name: str = None):
        #channel = self.client.get_channel(ctx.message.channel.id)
        channel = ctx.message.channel
        id_ = str(ctx.message.author.id)
        stockKeyList = []
        stockValueList = []
        stockWealth = []
        stockProfit = []
        stockProfitPercent = []
        stockOriginalValue = []
        times = []
        outputMsg = ''
        checkMsg = ''
        x = 0
        t0 = time.time()

        if stock_name != None:
            if stock_name.upper() not in self.client.userStocks[id_]['stocks']:
                return await ctx.send("You don't have that stock!")
            outputMsg = (f"**{stock_name.upper()}** : {self.client.userStocks[id_]['stocks'][stock_name.upper()]:,} : $" + 
            f"{self.client.userStocks[id_]['stocks'][stock_name.upper()] * GetStockPrice(stock_name.upper()):,.2f}")
        
        else:
            if 'stocks' not in self.client.userStocks[id_] or self.client.userStocks[id_]['stocks'] == {}:
                return await ctx.send("You don't have any stocks!")
            for key in self.client.userStocks[id_]['stocks'].keys():
                stockKeyList.append(key)
            
            i = 0
            while i < len(stockKeyList): # while loop that appends the stock amount person owns to stockValueList   
                stockValueList.append(self.client.userStocks[id_]['stocks'][stockKeyList[i]]['amount'])
                i += 1

            checkMsg = await ctx.send(f"Gathering your stocks info . . . {ctx.message.author.mention}")
            for wealth, stockName in zip(stockValueList, stockKeyList):
                stockWealth.append(wealth * GetStockPrice(stockName))
                t1 = time.time()
                total = t1 - t0
                times.append(total)
                newMsg = f"Checking stock {x + 1} of {len(stockKeyList)} | ETA: {(times[0] * (len(stockKeyList) + 1)) - total:.2f}s {ctx.message.author.mention}"
                x += 1

            if x == len(stockKeyList):
                t1 = time.time()
                total = t1 - t0
                await checkMsg.edit(content = f"COMPLETE | Time Elapsed: {total:.2f}s")
            elif x != len(stockKeyList):
                await checkMsg.edit(content = newMsg)

            z = 0
            for profit in stockWealth:
                stockProfit.append(float(profit) - (self.client.userStocks[id_]['stocks'][stockKeyList[z]]['amount'] * 
                                            self.client.userStocks[id_]['stocks'][stockKeyList[z]]['Price Per Share']))
                stockProfitPercent.append(round(((float(profit) - (self.client.userStocks[id_]['stocks'][stockKeyList[z]]['amount'] * 
                                            self.client.userStocks[id_]['stocks'][stockKeyList[z]]['Price Per Share'])) /
                                            (self.client.userStocks[id_]['stocks'][stockKeyList[z]]['amount'] *
                                            self.client.userStocks[id_]['stocks'][stockKeyList[z]]['Price Per Share'])) * 100, 2))
                stockOriginalValue.append(self.client.userStocks[id_]['stocks'][stockKeyList[z]]['Price Per Share'] *
                                        self.client.userStocks[id_]['stocks'][stockKeyList[z]]['amount'])
                z += 1
            
            i = 0
            trendEmoji = ''
            for x in stockProfit[0:12]:
                if x < 0:
                    trendEmoji = ":chart_with_downwards_trend:"
                elif x > 0:
                    trendEmoji = ":chart_with_upwards_trend:"
                else:
                    trendEmoji = ":scales:"
                outputMsg += (f'**{str(stockKeyList[i])}**' + ' | ' + f'{int(str(stockValueList[i])):,}' + ' | ' + f"${float(str(stockWealth[i])):,.2f}" + 
                              ' | ' + f'${float(str(stockProfit[i])):+,.2f}' + ' | ' + f'({float(str(stockProfitPercent[i])):+,.2f}%)' + f"\t** **{trendEmoji}" +
                              '\n')
                i += 1

            overallChange = sum(stockProfit)
            overallChangePercent = (round(sum(stockWealth) - sum(stockOriginalValue)) / sum(stockOriginalValue) * 100)
            trendThumbnail = ''
            if overallChange < 0:
                trendEmojiOverall = ":chart_with_downwards_trend:"
                trendThumbnail = 'https://cdn.discordapp.com/attachments/316967249716051969/715943797837660190/unknown.png'
            elif overallChange > 0:
                trendEmojiOverall = ":chart_with_upwards_trend:"
                trendThumbnail = 'https://cdn.discordapp.com/attachments/316967249716051969/715943755068211291/unknown.png'

        currentPage = 1
        pages = math.floor(len(stockKeyList)/12) + 1
        if pages < 1:
            pages = 1
        embed = discord.Embed(title = f"Overall Value: ${sum(stockWealth):,.2f} | " + 
                            f"${overallChange:+,.2f} | ({overallChangePercent:+,.2f}%) {trendEmojiOverall}", color = 0xdaa520)
        embed.add_field(name = "Stock | Amount | Total Value | Value Change | Percent Change",
                        value = f"{outputMsg}",
                        inline = True)
        embed.add_field(name = "="*10, 
                        value = f"{ctx.message.author.mention}",
                        inline = False)
        embed.set_footer(text = "Page")
        embed.set_thumbnail(url=trendThumbnail)
        
        indexRangeNum1 = 12
        indexRangeNum2 = 24
        currentPage = 1
        n = indexRangeNum1
        outputMsg = ''
        embed_2 = ''
        if len(stockKeyList) > 12:
            for x in stockProfit[indexRangeNum1:indexRangeNum2]:
                if x < 0:
                    trendEmoji = ":chart_with_downwards_trend:"
                elif x > 0:
                    trendEmoji = ":chart_with_upwards_trend:"
                else:
                    trendEmoji = ":scales:"
                outputMsg += (f'**{str(stockKeyList[n])}**' + ' | ' + f'{int(str(stockValueList[n])):,}' + ' | ' + f"${float(str(stockWealth[n])):,.2f}" + 
                              ' | ' + f'${float(str(stockProfit[n])):+,.2f}' + ' | ' + f'({float(str(stockProfitPercent[n])):+,.2f}%) ' + f"\t** **{trendEmoji}" +
                              '\n')
                n += 1
                currentPage += 1
            #outputMsg = '' # resets outputMsg from above to be used in pages of stocks
            embed_2 = discord.Embed(title = f"Overall Value: ${sum(stockWealth):,.2f} | " + 
                f"${overallChange:+,.2f} | ({overallChangePercent:+,.2f}%) {trendEmojiOverall}", color = 0xdaa520)
            embed_2.add_field(name = "Stock | Amount | Total Value | Value Change | Percent Change",
                                value = f"{outputMsg}",
                                inline = True)
            embed_2.add_field(name = "="*10, 
                                value = f"{ctx.message.author.mention}",
                                inline = False)
            embed_2.set_footer(text = "Page")
            embed_2.set_thumbnail(url=trendThumbnail)
            embeds = [
                embed,
                embed_2
            ]
        else:
            embeds = [embed]

        paginator = BotEmbedPaginator(ctx, embeds)
        await paginator.run()

    @commands.command()
    async def myreturns(self, ctx): # This command's information is pulled from UserStockReturns() in StockScraper.py
        channel = ctx.message.channel
        id_ = str(ctx.message.author.id)
        trendEmoji = None
        numberSign = None
        if float(UserStockReturns(id_)[0]) < 0:
            trendEmoji = ":chart_with_downwards_trend:"
            numberSign = '-'
        elif float(UserStockReturns(id_)[0]) > 0:
            trendEmoji = ":chart_with_upwards_trend:"
            numberSign = '+'
        else:
            trendEmoji = ":scales:"

        embed = discord.Embed(title = "Your All Time Returns", color = 0xdaa520)
        embed.add_field(name = "Return Amount | Return Amount Percent", 
                        value = f"{numberSign}${UserStockReturns(id_)[0]:,.2f} | ({UserStockReturns(id_)[1]:+,.2f}%) {trendEmoji}")
        await channel.send(content=None, embed=embed)

                   
    @commands.command()
    async def buystock(self, ctx, stock_name: str, amount: str):
        channel = ctx.message.channel
        id_ = str(ctx.message.author.id)
        stock_name = stock_name.upper()
        stockPrice = GetStockPrice(stock_name)
        maxAffordableAmount = math.floor(self.client.jahcoins[id_]['coins'] / stockPrice)
        currentDate = dt.datetime.today().strftime('%Y-%m-%d')
        currentTime = dt.datetime.now().strftime('%H:%M:%S')
        amountCheck = amount.isdigit()
        buyPrice = None
        if amountCheck == True:
            buyPrice = stockPrice * int(amount)
        if id_ in self.client.jahcoins:
            if id_ not in self.client.userStocks:
                self.client.userStocks[id_]= {}
                self.save_file_stocks()
            if 'stocks' not in self.client.userStocks[id_]:
                self.client.userStocks[id_]['stocks'] = {}
                self.save_file_stocks()

            else:
                #buyPrice = stockPrice * amount
                if amountCheck == True and self.client.jahcoins[id_]['coins'] < (stockPrice * int(amount)) or amount.upper() == 'MAX':
                    if maxAffordableAmount < 1:
                        return await ctx.send(f"You don't have enough to buy that many {stock_name} {ctx.message.author.mention}")
                    else:
                        buyPrice = stockPrice * maxAffordableAmount
                        amount = int(maxAffordableAmount)
                if stock_name not in self.client.userStocks[id_]['stocks']:
                    stockDictionary = {stock_name.upper() : {'amount': int(amount), 'Price Per Share': stockPrice}}
                    self.client.userStocks[id_]['stocks'].update(stockDictionary)
                    self.client.jahcoins[id_]['coins'] -= buyPrice
                    #self.save_file_coins(), self.save_file_stocks(), self.insert_StockBuyHistory(id_, currentDate, currentTime, stock_name, amount, buyPrice, stockPrice)
                    #stockDictionary = {}
                elif stock_name in self.client.userStocks[id_]['stocks']:
                    self.client.userStocks[id_]['stocks'][stock_name.upper()]['amount'] += int(amount)
                    self.client.jahcoins[id_]['coins'] -= buyPrice
            
            self.save_file_coins(), self.save_file_stocks(), self.insert_StockBuyHistory(id_, currentDate, currentTime, stock_name, int(amount), round(buyPrice, 4), stockPrice)
            
            return await ctx.send(f"Successfully bought {int(amount):,} {stock_name} for ${buyPrice:,.2f} " + 
                                    f" Price Per Share: ${stockPrice:,} {ctx.message.author.mention}")


    @commands.command()
    async def sellstock(self, ctx, stock_name: str, amount: str = None):
        channel = ctx.message.channel
        id_= str(ctx.message.author.id)
        stock_name = stock_name.upper()
        sellPrice = 0
        currentDate = dt.datetime.today().strftime('%Y-%m-%d')
        currentTime = dt.datetime.now().strftime('%H:%M:%S')

        if id_ in self.client.jahcoins:
            # if stock_name not in self.client.userStocks[id_]['stocks']:
            #   await ctx.send(f"You don't own that stock! {ctx.message.author.mention}")
            # else:
            stockPrice = GetStockPrice(stock_name)
            if amount.upper() == 'ALL':
                amount = self.client.userStocks[id_]['stocks'][stock_name]['amount']
            elif int(amount) > self.client.userStocks[id_]['stocks'][stock_name]['amount']:
                amount = int(self.client.userStocks[id_]['stocks'][stock_name]['amount'])
            else:
                amount = int(amount)
            
            sellPrice = amount * stockPrice
            self.client.userStocks[id_]['stocks'][stock_name]['amount'] -= amount
            
            if self.client.userStocks[id_]['stocks'][stock_name]['amount'] == 0:
                del self.client.userStocks[id_]['stocks'][stock_name]
            
            self.client.jahcoins[id_]['coins'] += sellPrice
            self.save_file_coins(), self.save_file_stocks(), self.insert_StockSellHistory(id_, currentDate, currentTime, stock_name, amount, round(sellPrice, 4))
            profitMade = self.get_StockProfit(id_, stock_name)[0]
            profitMadePercent = self.get_StockProfit(id_, stock_name)[1]
            trendEmoji = ''
            if profitMade < 0:
                trendEmoji = ":chart_with_downwards_trend:"
                wordProfitLoss = 'a loss'
            elif profitMade > 0:
                trendEmoji = ":chart_with_upwards_trend:"
                wordProfitLoss = 'a profit'
            else:
                trendEmoji = ":scales:"
                wordProfitLoss = 'no change'
            await ctx.send(f"Successfully sold {amount:,} {stock_name} for ${sellPrice:,.2f}\n" + 
                            f"You made {wordProfitLoss} of **${profitMade:+,.2f}** | %({profitMadePercent:+,.2f}) {trendEmoji} {ctx.message.author.mention}")
    
    # @sellstock.error
    # async def sellstock_error(self, ctx, error):
    #   id_ = str(ctx.message.author.id)
    #   if (error, KeyError or ValueError):
    #       await ctx.send(f"Be sure to type ``!sellstock [Stock Name] [Sell Amount('all' for all said stock)]`` If It still doesn't work " + 
    #           f"then that specific stock likely doesn't exist or you don't own that stock {ctx.message.author.mention}")


    @commands.command()
    async def profithistory(self, ctx, stockName: str):
        id_ = str(ctx.message.author.id)
        self.get_StockProfit(id_, stockName)
        return
        
    @commands.command()
    async def stockhelp(self, ctx):
        id_ = str(ctx.message.author.id)
        embed = discord.Embed(title = "AwnBot Stocks Tutorial", color = 0xdaa520)
        embed.add_field(name = "=== Introduction ===", 
                        value = f"""**AwnBot Stocks** allows you to simulate purchasing stocks from the actual stock market.\n
                        The currency that is used is called Jahcoins. Be sure to type !register to register yourself and to obtain
                        free starting jahcoins if you haven't already.\n The information of a given stock is pulled from Google's Finance API in real time.\n
                        The overall goal of AwnBot stocks is to allow a user to trade stocks without risking real money. As a result, this will hopefully
                        help many users gain the practice and knowledge to start trading real money after they are comfortable with how they are doing.""", 
                        inline = False)
        embed.add_field(name = "=== Commands ===", 
                        value = """**!stock [stockName]** Use this command to obtain the current price of a stock. However,
                        it is highly recommended to utilize www.robinhood.com or some other real time stock viewer.\n
                        **!buystock [stockName] [amountToBuy]** Use this command to purchase a stock.\n
                        **!sellstock [stockName] [amountToSell]** Use this command to sell a particular stock. NOTE: If you'd like to 
                        sell all of a specific stock, just type 'all' for the amount.\n
                        **!mystocks** This will show you the current stocks you the following: \n
                        1) All of the stocks you own\n2) The equity you have in each stock.\n3) Your overall portfolio value.\n
                        NOTE: **!mystocks** currently takes a while to check each stock. I am actively working on a faster solution to this issue
                        if one exists.""", inline = False)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/316967249716051969/714579925826535424/maxresdefault.png")
        await ctx.send(content = None, embed=embed)


def setup(client):
    client.add_cog(stocks(client))