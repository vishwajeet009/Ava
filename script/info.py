import os
import time
import re
import discord
from discord.ext import commands
from pymongo import MongoClient
from .log import log_emit

uri = os.getenv('MONGODB')
mongodb = MongoClient(uri)
db = mongodb[os.getenv("DOCUMENT")]
apidb = mongodb["API"] 

server = int(os.getenv("SERVER"))
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))
DEBUG = (os.getenv("DEBUG","") != "False" )

def match(a, b):
    l = min(len(a), len(b))
    a1 = a[:l].lower()
    b1 = b[:l].lower()
    if(a1 == b1):
        return True
    return False

def userdetail(user):
        details = f"Name : {user['name']}\nEntry Number : {user['entry']}\nDiscord Id : {user['discordid']}\nUserName : {user['username']}\n\n"
        return details

class Infos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        global logs, guild
        guild = self.bot.get_guild(int(server))
        logs = log_emit(LOG_CHANNEL, self.bot, DEBUG)

    @commands.command()
    @commands.has_role('Verified')
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def info(self, ctx,member : str):
        if(len(member) < 3):
            return await ctx.send(f"{ctx.author.mention} Pls enter minimum of 3 charaters")
        con = False
        _isrole = False
        if(re.search("^<@!.*>$", member)):
            userid = member[3:-1]
            con = True
        elif(re.search("^<@.*>$", member)):
            if(member[2] == '&'):
                return await ctx.send(f"{ctx.author.mention} Invalid Mention")
            userid = member[2:-1]
            con = True
        elif(member.isnumeric()):
            userid = member
            con = True
        if(con):
            users = db.member.find({"discordid" : userid},{"name" : 1, "entry" : 1, "discordid" : 1, "username" : 1})
            users_len = 0
            out = ""
            for user in users:
                users_len += 1
                out = out + userdetail(user)
            if(out == ""):
                out = "\tSorry no Member found"
            out = "```" + out + "```"
            await ctx.send(out)
            if(users_len > 1):
                dev_role = discord.utils.get(guild.roles, name="Core Team") 
                await logs.print(f"{dev_role.mention} Error occured in searching userid {userid}. If you seeing this plz report this to ADMIN ASAP.")  
        else:
            all_users = db.member.find({}, {"name" : 1, "entry" : 1, "discordid" : 1, "username" : 1})
            users = []
            for user in all_users:
                if(match(member, user['name']) or match(member, user['username'])):
                    users.append(user)
            out = ""
            for user in users:
                out = out + userdetail(user)
            if(len(users) == 0):
                out = "\tSorry no Member found"
            else:
                out = f"Found total {len(users)}\n\n" + out
            out = "```" + out + "```"
            await ctx.send(out)

    @commands.command()
    @commands.has_role('Verified')
    @commands.cooldown(1, 15, commands.BucketType.channel)
    async def members(self, ctx,role : str):
        try:
            roleid = role[3:-1]
            _role = guild.get_role(int(roleid))
            all_members = _role.members
        except:
            return await ctx.send(f"{ctx.author.mention} Invalid Role")
        all_users = db.member.find({}, {"name" : 1, "entry" : 1, "discordid" : 1})
        user_dic = {}
        for user in all_users:
            user_dic[user['discordid']] = (user['name'], user['entry'])
        out = f"Total {len(all_members)} members found\n\n"
        out_arr = []
        for member in all_members:
            try:
                detail = user_dic[str(member.id)]
            except:
                continue
            name = detail[0][:15]
            entry = detail[1]
            between = " " * (15 - len(name))
            tem = f"{name}{between}\t{entry}"
            out = out + tem + "\n"
            if(len(out) > 1800):
                out_arr.append(out)
                out = ""
        if(len(out) > 0):
            out_arr.append(out)
        for i in out_arr:
            await ctx.send(f'```{i}```')
    
    @commands.command()
    @commands.has_role('Core Team')
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def update(self, ctx):
        _role = discord.utils.get(guild.roles, name="Verified")
        all_members = _role.members
        all_users = db.member.find({}, {"name" : 1, "entry" : 1, "discordid" : 1})
        user_dic = {}
        for user in all_users:
            user_dic[user['discordid']] = (user['name'], user['entry'])
        final_mem = {} 
        insert_mem = []   
        for member in all_members:
            try:
                detail = user_dic[str(member.id)]
            except:
                continue
            name = detail[0]
            entry = detail[1]
            final_mem[entry] = {
                'name' : name,
                'discord-id' : str(member.id),
                'username' : member.name +'#'+member.discriminator,
                'img' : str(member.avatar_url) 
            }
        apidb.current.delete_many({})
        for i in final_mem:
            tem = final_mem[i]
            tem['entry'] = i
            insert_mem.append(tem)
        apidb.current.insert_many(insert_mem)
        return await ctx.send("Database forcefully Updated")


def setup(bot):
    print("info command added")   
    bot.add_cog(Infos(bot))
