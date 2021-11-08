import discord  # Main import
import asyncio  # Used in bitte werwolf
import asyncpraw  # Used in bitte meme
import asyncprawcore
from sys import exit  # Used in exit
from discord.ext import commands  # Main import for bot
from discord.ext.tasks import loop  # Used to time events
from discord import VoiceClient
from random import randrange, choice, seed, randint  # Used by all randoms
from datetime import datetime, timedelta  # Used to dertermine time (bitte weisheit, punish usw.)
import requests  # Used in bitte news
from bs4 import BeautifulSoup  # Used in bitte news
from gtts import gTTS  # used in bitte sprich
import ctypes
import ctypes.util
import os
from dotenv import load_dotenv
from mcstatus import MinecraftServer

local = os.path.isfile("isthislocal.txt")
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

if not local:
    print("ctypes - Find opus:")
    find_opus = ctypes.util.find_library('opus')
    print(find_opus)

    print("Discord - Load Opus:")
    load_opus = discord.opus.load_opus(find_opus)
    print(load_opus)

    print("Discord - Is loaded:")
    opus_loaded = discord.opus.is_loaded()
    print(opus_loaded)

# Enviroment Variables ------------------------------------

TOKEN = os.environ["TOKEN"]
default_status = os.environ["DEFAULT_STATUS"]
reddit_username = os.environ["REDDIT_USERNAME"]
reddit_password = os.environ["REDDIT_PASSWORD"]
reddit_id = os.environ["REDDIT_ID"]
reddit_secret = os.environ["REDDIT_SECRET"]
mc_ip = os.environ["MC_IP"]

# Setup ------------------------------------

jmjversion = "1.7.0.002"  # <Grand Release>.<Major Release/Big Update>.<Big fix/Small Update>.<Commit>
intents = discord.Intents.default()
intents.members = True

description = '''Discord Bot for JmJ Server'''
bot_prefixes = ["bitte ", "Bitte ", "BITTE "] if not local else ["."]
bot = commands.Bot(command_prefix=bot_prefixes, description=description, intents=intents, case_insensitive=True)
bot.remove_command("help")
reddit = asyncpraw.Reddit(client_id=reddit_id, client_secret=reddit_secret, password=reddit_password,
                          user_agent=f"firefox:jmj asyncpraw request (by u/{reddit_username})",
                          username=reddit_username)


@bot.event
async def on_ready():
    print('-' * len(f"Version: {jmjversion}"))
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(f"Version: {jmjversion}")
    print('-' * len(f"Version: {jmjversion}"))

    await bot.change_presence(activity=discord.Game(name=default_status))
    # await bot.get_channel(771304596924268555).send(
    # choice(["Bot ist aufgewacht und motiviert!", "Ein wildes Bot erscheint!"]))


# Vars ------------------------------------

g_running = False  # Bool if game of galgen is running
g_guessed = []  # Chars guessed for current game of galgen
g_word = ""  # galgen word
g_fail = 0  # galgen fails
g_msg = [None, None, None]  # reference to galgen message
g_comm = []  # reference to all called commands for galgen game
wunsch = ""  # wunsch of bot for make-a-wish
pinned = None  # reference to currently pinned among us code
amongmsg = None  # reference to current among us bot message
punished = []  # [punished member, time still punished]
timedmsg = []  # contains [reference to message, datetime until deleted]
voiceclient = None  # current voiceclient of bot
last_meme = None  # reference to last submission posted by bot
last_meme_voted = 0  # counter for votes for last submission: {-1, 0, +1}
last_meme_embed = None  # reference to last embed of last meme


# Methods ------------------------------------

def getchannel(channel_id: str):
    channel_str = channel_id[2:len(channel_id) - 1]
    if not channel_str.isdigit():
        return None
    return bot.get_channel(int(channel_str))


def embed_from_submission(submission: asyncpraw.models.Submission):
    global last_meme, last_meme_voted

    vembed = discord.Embed(title=submission.title, colour=discord.Colour.orange(),
                           url=submission.shortlink)
    if submission.selftext != "":
        vembed = discord.Embed(title=submission.title, colour=discord.Colour.orange(),
                               description=submission.selftext, url=submission.shortlink)
    else:
        vembed.set_image(url=submission.url)
    vembed.set_footer(text=f"{submission.score} Hochwählies\n" +
                           f"By: u/{submission.author.name}\n" +
                           f"Sub: r/{submission.subreddit.display_name}\n" +
                           f"Link: {submission.shortlink}")

    last_meme = submission
    last_meme_voted = 0
    return vembed


def print_embed(embed: discord.Embed):
    return {
        "title": embed.title,
        "description": embed.description,
        "author": embed.author,
        "color": embed.color,
        "fields": embed.fields,
        "footer": embed.footer,
        "image": embed.image,
        "thumbnail": embed.thumbnail
    }


# Commands (Help) ------------------------------------

@bot.command(aliases=["help"])
async def help_(ctx):
    await ctx.send("Versuchs lieber mit bitte hilfe. Wir sind ja ein deutscher Server :wink:")


@bot.command(aliases=["hilf"])
async def hilfe(ctx):
    vembed = discord.Embed(title="JmJ Bot | Übersicht der Kommandos", colour=discord.Colour.blue())
    # vembed.add_field(name="bitte ", value="", inline=False)
    vembed.add_field(name="bitte avanti <@person>", value="Wer will zuerst liegen?", inline=False)
    vembed.add_field(name="bitte bestrafe <@person>", value="Einen Spieler bestrafen. Achtung: Gibt schlechtes Karma!",
                     inline=False)
    vembed.add_field(name="bitte hygiene", value="Wichtige Tipps zur Hygiene.", inline=False)
    vembed.add_field(name="bitte galgen <kategorie>",
                     value="Eine Runde Galgenmännchen spielen. Verfügbare Kategorien: deutsch, zuhause, minecraft",
                     inline=False)
    vembed.add_field(name="bitte geheim", value="Ein Geheimnis enthüllen.", inline=False)
    vembed.add_field(name="bitte gumo", value="Einen Guten Morgen wünschen.", inline=False)
    vembed.add_field(name="bitte gumi", value="Einen Guten Mittag wünschen.", inline=False)
    vembed.add_field(name="bitte guna", value="Eine Gute Nacht wünschen.", inline=False)
    vembed.add_field(name="bitte gumina",
                     value="Eine Gute Geisterstunde wünschen (kann nur um 3 Uhr nachts ausgeführt werden!)",
                     inline=False)
    vembed.add_field(name="bitte make-a-wish", value="Dem Bot einen Wunsch gewähren.", inline=False)
    vembed.add_field(name="bitte meme [subreddit | id]", value="Zeige ein zufälliges Meme.", inline=False)
    vembed.add_field(name="bitte hochwaehl", value="Wähle das letzte Meme hoch. (haha)", inline=False)
    vembed.add_field(name="bitte runterwaehl", value="Wähle das letzte Meme runter. (nicht lustig)", inline=False)
    vembed.add_field(name="bitte minecraft <status | start | ping> ",
                     value="Zeige wer gerade auf dem Minecraft Server online ist.", inline=False)
    vembed.add_field(name="bitte news", value="Zeige einen seriösen Nachrichtenartikel.", inline=False)
    vembed.add_field(name="bitte ping", value="Den Ping abfragen.", inline=False)
    vembed.add_field(name="bitte punish <@person>", value="Eine Person bestrafen.", inline=False)
    vembed.add_field(name="bitte vergeben", value="Von seiner Bestrafung erlöst werden.", inline=False)
    vembed.add_field(name="bitte react [zeichenfolge]",
                     value="Mit Emojis reagieren. Max. 20 Zeichen ohne Wiederholungen.",
                     inline=False)
    vembed.add_field(name="bitte sprich <text>", value="Der Bot kann sprechen!", inline=False)
    vembed.add_field(name="bitte sound <sound>", value="Der Bot kann Töne machen!", inline=False)
    vembed.add_field(name="bitte geh", value="Der Bot hat zu Ende gesprochen!", inline=False)
    vembed.add_field(name="bitte status <desc>", value="Den Status des Bots auf <desc> setzen. [VIP]", inline=False)
    vembed.add_field(name="bitte vergeben", value="Erlöse dich nach fünf Minuten von deinen Sünden.", inline=False)
    vembed.add_field(name="bitte version", value="Zeige die Version und den Quellkot des Bots", inline=False)
    vembed.add_field(name="bitte weisheit", value="Die Weisheit der Stunde ausgeben.", inline=False)
    vembed.add_field(name="bitte werwolf", value="Eine Runde Werwolf spielen.", inline=False)
    await ctx.send(embed=vembed)


# Bot event ------------------------------------

@bot.event
async def on_member_join(member):
    print(f"New Member {member.name} in {member.guild}")
    wchannel = member.guild.system_channel
    await wchannel.send("new phone who dis")


@bot.event
async def on_message(msg):
    # general log
    if len(msg.embeds) > 0:
        for embed in msg.embeds:
            print("<%s at %s in %s(%s)> : %s" % (
                msg.author, datetime.now().strftime("(%y/%m/%d %H:%M:%S)"), msg.channel, msg.channel.id,
                print_embed(embed)))
    else:
        print("<%s at %s in %s(%s)> : %s" % (
            msg.author, datetime.now().strftime("(%y/%m/%d %H:%M:%S)"), msg.channel, msg.channel.id,
            msg.content))

    # Don't process bot messages
    if msg.author.bot:
        return

    # Detect wierdly used prefixes
    if msg.content.lower().startswith("bitte ") and msg.content[:6] not in bot_prefixes and not local:
        await msg.channel.send(f"{msg.content[:6]} verwende den Prefix 'bitte' und nicht {msg.content[:6]}")
        return

    # Friendly reminder that the prefix was changed
    if msg.content.startswith("!"):
        await msg.channel.send(
            "Hey du Neanderthaler. Falls du gerade erst aus deinem Winterschlaf erwacht bist, hier ein Hinweis für "
            "dich:\nIch reagiere ab jetzt nur noch auf höfliche Anfragen, die mit 'bitte' anfangen.\nLiebe "
            "Grüße\nDein Lieblingsbot😘")

    # Punished message
    global punished, timedmsg
    if punished:
        vergebung = msg.content.lower() == "bitte vergeben" or msg.content.lower() == "bitte begnadigen" if not local \
            else msg.content.lower() == ".vergeben" or msg.content.lower() == ".begnadigen"
        if msg.author.id is punished[0] and not vergebung:
            temp = await msg.channel.send(f"> {msg.author.display_name}: {msg.content}\nSchande!")
            timedout = datetime.now() + timedelta(seconds=10)
            timedmsg.append([temp, timedout])
            await msg.delete()
            return

    # pin current among us code
    if len(msg.content) == 6 and msg.content.isupper() and msg.content.isalpha():
        global pinned, amongmsg
        msglst = ["Wow. Ich hab einen Unter Uns Code gefunden. Den heb ich auf!",
                  "Viel Spaß beim der Runde Among Us. Ich speicher euch den Code.",
                  "Tim sus."]
        if pinned is not None:
            dmsg = []
            try:

                dmsg.append(pinned)
                async for botmsg in msg.channel.history(limit=100):
                    if botmsg.type == discord.MessageType.pins_add and botmsg.author.bot:
                        dmsg.append(botmsg)
                dmsg.append(amongmsg)
                await msg.channel.delete_messages(dmsg)
            except discord.errors.NotFound:
                pass
        pinned = msg
        amongmsg = await msg.channel.send(choice(msglst))
        await msg.pin()

    global last_meme
    if last_meme is not None:
        if "haha" in msg.content.lower():
            await hochwaehl(msg.channel)
        elif "unlustig" in msg.content.lower():
            await runterwaehl(msg.channel)

    # make a wish
    global wunsch
    if msg.content == "<:cakee:771165204461125663>" and wunsch == "kuchen":
        await msg.channel.send("Danke %s. Du hast mir meinen Wunsch erfüllt" % msg.author.display_name)
        wunsch = ""
    elif msg.content == "<:pizzza:771165145262850088>" and wunsch == "pizza":
        await msg.channel.send("Mhhh. Die Pizza schmecht vorzüglich! Danke %s" % msg.author.display_name)
        wunsch = ""
    elif ((msg.content == "<:cakee:771165204461125663>" or msg.content == "<:pizzza:771165145262850088>")
          and wunsch == ""):
        await msg.channel.send("Danke, aber ich bin gerade wunschlos glücklich!")
    else:
        await bot.process_commands(msg)


@loop(seconds=0.5)
async def always_active():
    # Always
    global timedmsg
    delete_msg = []
    for tmsg in timedmsg:
        if tmsg[1] <= datetime.now():
            delete_msg.append(tmsg[0])
            timedmsg.remove(tmsg)

    for dmsg in delete_msg:
        try:
            await dmsg.delete()
        except discord.errors.NotFound:
            pass


# Commands for all ------------------------------------

@bot.command()
async def avanti(ctx, *, member):
    # Ich kann dich gerne zu avanti fahren
    memberid = member
    for members in ctx.channel.members:
        if member.lower() == members.display_name.lower():
            memberid = "<@!" + str(members.id) + ">"
    avantilst = ["%s liegt als erstes" % memberid, "Wehe ich sehe %s heute noch an der Kirche." % memberid,
                 "Hör auf zu jammern %s, ich kann dich auch zu Avanti fahren." % memberid]
    await ctx.send(choice(avantilst))


@bot.command()
async def geheim(ctx):
    # send secret link via private message
    await ctx.send("Psssst :shushing_face:")
    await ctx.author.send("<https://www.youtu.be/dQw4w9WgXcQ>")


@bot.command()
async def gumo(ctx):
    # Einen guten Morgen wünschen
    vgumo = [
        "Ich wünsche allen einen herrlichen guten Morgen.",
        "Guten Morgen, na wie habt ihr geschlafen?",
        "Eine Runde Bierpong am Morgen vertreibt Kummer und Sorgen! :beers:",
        "Einen super sonnigen und tollen Tag wünsche ich euch! :sunny:",
        "AUFSTEHN IST SCHÖN :musical_note:\nwer sagt das\nAUFSTEHN IST SCHÖN :musical_note:\nund heimlich die Familie "
        "noch schlafen sehn\nAUFSTEHN IST SCHÖN :musical_note:\nwer sagt das\nAUFSTEHN IST SCHÖN :musical_note:\nund "
        "der liebste Klang der Welt das ist für mich:\nWENN DER WECKER SCHELLT!!! :musical_note:"]
    await ctx.send(choice(vgumo))


@bot.command()
async def gumi(ctx):
    # Einen guten Mittag wünschen
    vgumi = [
        "Ahh, endlich Mittag. Es ist so herrlich!",
        "Eine fröhliche Mittagspause wünsche ich euch.",
        "Guten Mittag! Ich wünschte ich hätte jetzt ein all-inclusive Buffet mit Getränken. :drool:"]
    await ctx.send(choice(vgumi))


@bot.command()
async def guna(ctx):
    # Eine gute Nacht wünschen
    vguna = [
        "Schlaft alle schön! :sleeping:",
        "Bis morgen. Ich gehe jetzt schlafen.",
        "Gute Nacht. Träumt alle schön von mir.",
        "Möge euch Kissen diese Nacht stets weich und kuschlig sein!"]
    await ctx.send(choice(vguna))


@bot.command()
async def gumina(ctx):
    # Eine Gute Geisterstunde wünschen (kann nur um 3 Uhr nachts ausgeführt werden!)
    vguna = ["Buuuuuuuh! :scream:", "Ein wildes Geist erscheint! :ghost:"]
    if datetime.now().strftime("%H") == "03":
        await ctx.send(choice(vguna))
    else:
        await ctx.send("Es ist noch nicht 3 Uhr, aber ich fühle gespenstische Geschehnisse! :cold_face:")


@bot.command(aliases=["guess", "g"])
async def guess_char(ctx, char: str):
    # spieler der errät erhält einen punkt?
    global g_running, g_guessed, g_word, g_fail, g_msg, g_comm
    char = char.lower()
    ascii_lowercase = "abcdefghijklmnopqrstuvwxyz"
    g_comm.append(ctx.message)
    timedmsg.append([ctx.message, datetime.now() + timedelta(seconds=10)])

    if not g_running:  # if a game is running
        await ctx.send("Es läuft gerade kein Galgenmännchen-Spiel. Starte ein neues mit 'bitte galgen'")
    elif char in ascii_lowercase:  # if input is viable
        if char in g_word:  # if input is in word
            if char not in g_guessed:  # if input is in word and not yet guessed -> right
                g_guessed.append(char)

                # Check if all letters have been guessed
                win = True
                for i in g_word.replace(" ", ""):
                    win &= i in g_guessed
                if win:  # all letters have been guessed
                    await g_msg[0].edit(content=f"Das Wort {g_word} wurde erraten!")
                    await gdisplay(ctx, g_guessed, g_word, g_fail)
                    dmsg = []
                    for comm in g_comm:
                        try:
                            dmsg.append(comm)
                        except discord.errors.NotFound:
                            pass
                    await ctx.channel.delete_messages(dmsg)
                    g_msg = [None, None, None]
                    g_running = False
                else:  # not all letters have been guessed
                    await g_msg[0].edit(content=f"Der Buchstabe {char} ist richtig!")
                    await gdisplay(ctx, g_guessed, g_word, g_fail)

            else:  # if input is in word but was already guessed
                await g_msg[0].edit(content=f"Der Buchstabe {char} wurde bereits geraten. Pass mal besser auf!")
        elif char not in g_guessed:  # if input is not in word and was not guessed before -> false
            g_fail += 1
            g_guessed.append(char)
            await g_msg[0].edit(content=f"Der Buchstabe {char} ist leider falsch.")
            await gdisplay(ctx, g_guessed, g_word, g_fail)
            if g_fail >= 8:  # check if you have lost
                await g_msg[0].edit(
                    content=f"Ohh nein! Das Galgenmännchen wurde nicht gerettet. Das Wort wäre {g_word} gewesen.")
                g_running = False
                dmsg = []
                for comm in g_comm:
                    try:
                        dmsg.append(comm)
                    except discord.errors.NotFound:
                        pass
                await ctx.channel.delete_messages(dmsg)
                g_msg = [None, None, None]
        else:  # if input is not in word but was already guessed before
            await g_msg[0].edit(content=f"Der Buchstabe {char} wurde bereits geraten. Pass mal besser auf!")
    else:  # no viable input
        await g_msg[0].edit(
            content=f"{char} ist keine gültige Eingabe. Bitte gib nur einen einzelnen Buchstaben ein (keine Umlaute)!")


@bot.command()
async def galgen(ctx, cat: str = "deutsch"):
    global g_running, g_guessed, g_word, g_fail, g_msg

    for msg in g_msg:
        if msg:
            await ctx.channel.delete_messages(g_msg)
            g_msg = [None, None, None]

    if not g_running:
        g_running = True
        g_guessed = []
        g_fail = 0
        # init words
        deutsch_lst = ["desoxyribonukleinsaeure", "schifffahrtskapitaensmuetzenfabrik", "wimmelbild", "axt",
                       "fernseher", "sonnenuntergang", "nahrungsmittel", "vollmond",
                       "gummibaerchen", "quizshow", "unterrichtsschluss", "rubbellos", "fussballweltmeisterschaft",
                       "haftpflichtversicherung", "zebra", "hund", "syntax", "photosynthese",
                       "zoologe", "photovoltaikanlage", "tierschutzverein", "lampe", "dokumentationszentrum",
                       "lokomotive", "konfetti", "clown", "wohnzimmer"]
        zuhause_lst = ["fernseher", "wohnzimmer", "esstisch", "deckenlampe", "tuer", "sofa", "buecherregal",
                       "schreibtisch", "steckdose", "heizung",
                       "bilderrahmen", "fenster", "rollladen", "blumentopf", "wasserkaraffe", "router", "waschmaschine",
                       "umzugskarton", "laptop", "kalender", "zeitung", "papiermuell",
                       "teppich", "bettdecke", "dusche", "kuscheltier", "lichtschalter", "einkaufstasche",
                       "kugelschreiber", "kochtopf", "herdplatte", "uhr"]
        minecraft_lst = ["diamond", "cobblestone", "mycelium", "oak planks", "spruce wood", "acacia fence",
                         "dark oak trapdoor", "jungle door", "netherwart block",
                         "netherite ore", "steve", "obsidian", "ender dragon", "zombie", "mending", "pufferfish",
                         "ender crystal", "glowstone", "dried kelp", "diamond sword", "wooden axe",
                         "golden chestplate", "villager"]

        if cat == "zuhause":
            g_word = choice(zuhause_lst)
        elif cat == "deutsch":
            g_word = choice(deutsch_lst)
        elif cat == "minecraft":
            g_word = choice(minecraft_lst)
        else:
            g_word = choice(deutsch_lst)
        g_msg[0] = await ctx.send(f"Neues Galgenmännchen-Spiel in der Kategorie {cat} wird gestartet.")

    else:
        g_msg[0] = await ctx.send("Es läuft bereits ein Galgenmännchen-Spiel.")
    await gdisplay(ctx, g_guessed, g_word, g_fail)


async def gdisplay(ctx, guesslst, word, fail):
    global g_msg

    formatted_word = ""  # Format Word
    for i in word:
        if i == " ":
            formatted_word += "| "
        elif i in guesslst:
            formatted_word += i + " "
        else:
            formatted_word += "_ "

    guessed = ""  # Format guessed
    for i in guesslst:
        guessed += i + ", "

    unicode = ["", "  ", "", "", "", "", ""]
    for i in range(fail):
        if fail > 0: unicode[0] = "\U0001f635"
        if fail > 1: unicode[2] = "\U0001f455"
        if fail > 2: unicode[1] = "\U0001f44b"
        if fail > 3: unicode[3] = "\U0001f44c"
        if fail > 4: unicode[4] = "\U0001fa73"
        if fail > 5: unicode[5] = "\U0001f45f"
        if fail > 6: unicode[6] = "\U0001f45f"
        if fail > 7: unicode[0] = "\U0001f480"
    unicode = tuple(unicode)

    if not g_msg[1]:
        g_msg[1] = await ctx.send("""```
              _____
            /       \\
           |        %s
           |      %s%s%s
           |        %s
           |       %s%s
           |
        __/ \\__
        ```""" % unicode)
    else:
        await g_msg[1].edit(content="""```
              _____
            /       \\
           |        %s
           |      %s%s%s
           |        %s
           |       %s%s
           |
        __/ \\__
        ```""" % unicode)
    if not g_msg[2]:
        g_msg[2] = await ctx.send(f"```Geratene Buchstaben: {guessed}\nWort: {formatted_word}\n"
                                  "Rate einen Buchstaben mit 'bitte g(uess) [buchstabe]'```")
    else:
        await g_msg[2].edit(content=f"```Geratene Buchstaben: {guessed}\nWort: {formatted_word}\n"
                                    "Rate einen Buchstaben mit 'bitte g(uess) [buchstabe]'```")


@bot.command()
async def hygiene(ctx):
    # return import information regarding hygiene
    vhygiene = [
        "Bitte regelmäßig Hände waschen!",
        "Ein Schluck Wein mit Schuss kann auch von innen desinfizieren.",
        "Mindestens 30 Sekunden Hände waschen!",
        "Desinftionsmittel ist nicht nur gut für die Hände, sondern auch für den Körper! :wine_glass:"]
    await ctx.send(choice(vhygiene))


@bot.command(aliases=["löschdich", "loeschdich"])
async def lenny(ctx):
    if local:
        path = "files/lenny_deepfry.jpg"
    else:
        path = "python/files/lenny_deepfry.jpg"
    await ctx.send(file=discord.File(path))


@bot.command(aliases=["lösch"])
async def loesch(ctx, string: str = None):
    if string == "dich" or string == "dich!":
        await lenny(ctx)


@bot.command(name="make")
async def wish(ctx, *, string: str = None):
    # Fulfill a wish to the bot when hour == minute (ex. 12:12)
    if string == "a wish":
        global wunsch
        if datetime.now().strftime("%H") == datetime.now().strftime("%M"):
            r = choice(["einen Kuchen", "ein Stück Pizza"])
            if r == "einen Kuchen":
                wunsch = "kuchen"
            elif r == "ein Stück Pizza":
                wunsch = "pizza"
            await ctx.send(
                "Danke %s für den freien Wunsch! Ich wünschen mir %s! :crystal_ball:" % (ctx.author.display_name, r))
        else:
            await ctx.send("Das funktioniert gerade nicht. Die Uhrzeit ist keine magische Zahl :cry:")


@bot.command(aliases=["maimai"])
async def meme(ctx, sub: str = None, amount: int = 1):
    # Send a random meme of the hot section of a certain subreddit (default: ich_iel)
    global last_meme, last_meme_voted, reddit, last_meme_embed
    meme_subs = ["ich_iel", "dankmemes", "memes", "lotrmemes", "me_irl",
                 "MinecraftMemes", "historyMemes", "trebuchetmemes"]

    if sub is None:
        sub = choice(meme_subs)
    else:

        try:
            amount = int(sub)
            sub = choice(meme_subs)
        except ValueError:
            pass

        try:
            submission = await reddit.submission(id=sub)
            last_meme_embed = await ctx.send(embed=embed_from_submission(submission))
            last_meme_voted = 0
            return
        except asyncprawcore.NotFound:
            pass

    __range__ = 50
    if amount < 1:
        await ctx.send("Haha sehr lustig 😑. Lach ich?")
        return
    elif amount > 5:  # Stop spamming
        await ctx.send("Ich hab nicht den ganzen Tag Zeit Memes zu schauen, also fahr mal deine Ansprüche runter.")
        return
    if sub.lower() == "random":
        subreddit = await reddit.random_subreddit()
        sub = subreddit.display_name
    async with ctx.channel.typing():
        try:
            reddit.subreddits.search_by_name(sub, exact=True)
            subreddit = await reddit.subreddit(sub, fetch=True)
            chosen = []
            for n in range(0, amount):
                post_to_pick = randint(0, __range__ - 1)
                while post_to_pick in chosen:
                    post_to_pick = randint(0, __range__ - 1)
                chosen.append(post_to_pick)
                submission = None
                count = 0
                async for post in subreddit.hot(limit=__range__):
                    if count == post_to_pick:
                        submission = post
                        break
                    count += 1
                if submission is None:
                    await ctx.send("Fehler.")
                    return
                # Last Meme Post = reference to embed
                last_meme_embed = await ctx.send(embed=embed_from_submission(submission))
                last_meme_voted = 0
        except asyncprawcore.BadRequest:
            await ctx.send("Ne will nicht.")
        except (asyncprawcore.NotFound, asyncprawcore.Redirect):
            await ctx.send("Gibt's nicht.")


@bot.command(aliases=["hochwähl", "upvote"])
async def hochwaehl(ctx):
    global last_meme, last_meme_voted

    if last_meme is None:
        await ctx.send("Find ich nicht mehr, will aber auch nicht suchen.")
        return

    if last_meme_voted == 1:
        await ctx.send("Dieses Meme wurde bereits gehochgewählt.")
        return

    try:
        if last_meme_voted == 0:
            await last_meme.upvote()
            last_meme = await reddit.submission(id=last_meme.id)  # Update submission
            await ctx.send(
                f"Yeah. Ich hab das letzte Maimai für dich gehochwählt!")
            await last_meme_embed.edit(embed=embed_from_submission(last_meme))
            last_meme_voted = 1
        elif last_meme_voted == -1:
            await last_meme.clear_vote()
            last_meme = await reddit.submission(id=last_meme.id)  # Update submission
            await ctx.send(f"Ok. Das Maimai ist jetzt wieder neutral bewertet.")
            await last_meme_embed.edit(embed=embed_from_submission(last_meme))
            last_meme_voted = 0

    except asyncprawcore.BadRequest:
        await ctx.send("Uff, Fehler.")


@bot.command(aliases=["runterwähl", "downvote"])
async def runterwaehl(ctx):
    global last_meme, last_meme_voted

    if last_meme is None:
        await ctx.send("Find ich nicht mehr, will aber auch nicht suchen.")
        return

    if last_meme_voted == -1:
        await ctx.send("Dieses Meme wurde bereits fertiggemacht 😞.")
        return

    try:
        if last_meme_voted == 0:
            await last_meme.downvote()
            last_meme = await reddit.submission(id=last_meme.id)  # Update submission
            await ctx.send(
                "Gefällt dir mein Maimai nicht😢? Ich hab es jedenfalls gerunterwählt.")
            await last_meme_embed.edit(embed=embed_from_submission(last_meme))
            last_meme_voted = -1
        elif last_meme_voted == 1:
            await last_meme.clear_vote()
            last_meme = await reddit.submission(id=last_meme.id)  # Update submission
            await ctx.send(f"Schade. Das Maimai ist jetzt wieder neutral bewertet.")
            await last_meme_embed.edit(embed=embed_from_submission(last_meme))
            last_meme_voted = 0

    except asyncprawcore.BadRequest:
        await ctx.send("Uff, Fehler.")


@bot.command(aliases=["news", "nachrichten", "zeitung"])
async def news_command(ctx, r: int = None):
    # print a random article from postillon
    url = "https://www.der-postillon.com/"
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, 'lxml')
    news = []

    # 1. Get all news items
    for element in soup.find_all("div", {"class": "post hentry"}):
        try:

            headline = element.find_all("a", href=True)[0].text.strip()
            if headline.find("Newsticker") != -1:
                continue

            body = element.find_all("p")[0] if len(element.find_all("p")) > 0 else \
                element.find_all(itemprop="articleBody")[0]

            newsitem = {"headline": headline,
                        "url": element.find_all("a", href=True)[0]["href"],
                        "body": body.text.strip(),
                        "image": element.find_all("img")[0]["src"]
                        }

            for item in newsitem:
                if item is None:
                    continue
            news.append(newsitem)
        except IndexError:
            continue

    # 2. Output News

    if len(news) == 0:
        await ctx.send("Nichts besonderes gefunden.")
        return

    # Debug
    if r == -69:
        await ctx.send(f"{len(news)} Artikel gefunden.")
        for article in news:
            embed = discord.Embed(title=article["headline"],
                                  description=article["body"],
                                  colour=discord.Colour.gold(),
                                  url=article["url"])
            embed.set_image(url=article["image"])
            await ctx.send(embed=embed)
        return

    if r is None:
        r = randint(0, len(news))
    elif r >= len(news):
        r = r % len(news)
    vembed = discord.Embed(title=news[r]["headline"],
                           description=news[r]["body"],
                           colour=discord.Colour.gold(),
                           url=news[r]["url"])
    vembed.set_image(url=news[r]["image"])
    await ctx.send(embed=vembed)


@bot.command()
async def ping(ctx):
    # Request ping
    await ctx.send("Pong!")


@bot.command(aliases=["bestrafe"])
async def punish(ctx, *, person: str = None):
    # Einen Spieler bestrafen!! Muhahah!
    global punished
    if punished:
        await ctx.send(
            f"{bot.get_user(punished[0]).display_name} ist derzeit bestraft. "
            "Warte bis dieser Nutzer um Vergebung bittet, um einen neuen Nutzer zu bestrafen.")
        return

    elif person is None:  # if no member specified choose one randomly
        members = ctx.channel.members
        for member in members:
            if member.bot:
                members.remove(member)
        member = choice(members)
        punished = [member.id, datetime.now() + timedelta(minutes=5)]
        await ctx.send(
            f"{member.display_name} wurde zufällig ausgewählt, um von {ctx.author.display_name} bestraft zu werden. "
            "Muhahahahaha!")
        return

    member_id = None
    if person.startswith("<@!"):
        person_id = person[3:len(person) - 1]
        for member in ctx.channel.members:
            if person_id == str(member.id):
                member_id = int(person_id)
                break
    else:
        for member in ctx.channel.members:
            if person.lower() == member.display_name.lower() or person.lower() == member.name.lower():
                member_id = member.id
                break

    if member_id:
        user = bot.get_user(member_id)
        if user.bot:
            await ctx.send(f"{user.name} ist zu mächtig, um bestraft zu werden, "
                           "und außerdem hat er gar nichts gemacht :(")
        else:
            punished = [member_id, datetime.now() + timedelta(minutes=5)]
            await ctx.send(f"{user.name} wurde von {ctx.author.display_name} bestraft. Muhahahaha!")
    else:
        punished = [ctx.author.id, datetime.now() + timedelta(minutes=5)]
        await ctx.send(f"{person} wurde nicht gefunden. Als Rache wurdest du selbst bestraft! *Noch mehr* Muhahahahah!")


@bot.command(aliases=["reagier"])
async def react(ctx, *, txt: str):
    # React to the last message with letter emojis
    msg = await ctx.history(limit=1, before=ctx.message).flatten()
    msg = msg[0]

    if txt.lower() == "ok":
        await msg.add_reaction("🆗")
        await ctx.message.delete()
        return
    if txt.lower() == "props" or txt.lower() == "100":
        await msg.add_reaction("💯")
        await ctx.message.delete()
        return

    lst = []
    ascii_lowercase = "abcdefghijklmnopqrstuvwxyz 0123456789"
    txt = txt.lower()
    for i in txt:
        if i in lst or i not in ascii_lowercase:
            if i in lst and i == "i" and "í" not in lst:
                lst.append("í")
            elif i in lst and i == "a" and "á" not in lst:
                lst.append("á")
            elif i in lst and i == "b" and "ü" not in lst:
                lst.append("ü")
            elif i in lst and (i == "0" or i == "o") and "ó" not in lst:
                lst.append("ó")
            elif i == "ä" and i not in lst:
                lst.append("ä")
            elif i == "ö" and i not in lst:
                lst.append("ö")
            elif i == "é" and i not in lst:
                lst.append("é")
            else:
                await ctx.send("Ne hab kein Bock!")
                return
        else:
            lst.append(i)

    await ctx.message.delete()
    for j in lst:
        if j == "a":
            await msg.add_reaction("\U0001F1E6")
        elif j == "b":
            await msg.add_reaction("\U0001F1E7")
        elif j == "c":
            await msg.add_reaction("\U0001F1E8")
        elif j == "d":
            await msg.add_reaction("\U0001F1E9")
        elif j == "e":
            await msg.add_reaction("\U0001F1EA")
        elif j == "f":
            await msg.add_reaction("\U0001F1EB")
        elif j == "g":
            await msg.add_reaction("\U0001F1EC")
        elif j == "h":
            await msg.add_reaction("\U0001F1ED")
        elif j == "i":
            await msg.add_reaction("\U0001F1EE")
        elif j == "j":
            await msg.add_reaction("\U0001F1EF")
        elif j == "k":
            await msg.add_reaction("\U0001F1F0")
        elif j == "l":
            await msg.add_reaction("\U0001F1F1")
        elif j == "m":
            await msg.add_reaction("\U0001F1F2")
        elif j == "n":
            await msg.add_reaction("\U0001F1F3")
        elif j == "o":
            await msg.add_reaction("\U0001F1F4")
        elif j == "p":
            await msg.add_reaction("\U0001F1F5")
        elif j == "q":
            await msg.add_reaction("\U0001F1F6")
        elif j == "r":
            await msg.add_reaction("\U0001F1F7")
        elif j == "s":
            await msg.add_reaction("\U0001F1F8")
        elif j == "t":
            await msg.add_reaction("\U0001F1F9")
        elif j == "u":
            await msg.add_reaction("\U0001F1FA")
        elif j == "v":
            await msg.add_reaction("\U0001F1FB")
        elif j == "w":
            await msg.add_reaction("\U0001F1FC")
        elif j == "x":
            await msg.add_reaction("\U0001F1FD")
        elif j == "y":
            await msg.add_reaction("\U0001F1FE")
        elif j == "z":
            await msg.add_reaction("\U0001F1FF")
        elif j == " ":
            await msg.add_reaction("🟦")
        elif j == "0":
            await msg.add_reaction("0️⃣")
        elif j == "1":
            await msg.add_reaction("1️⃣")
        elif j == "2":
            await msg.add_reaction("2️⃣")
        elif j == "3":
            await msg.add_reaction("3️⃣")
        elif j == "4":
            await msg.add_reaction("4️⃣")
        elif j == "5":
            await msg.add_reaction("5️⃣")
        elif j == "6":
            await msg.add_reaction("6️⃣")
        elif j == "7":
            await msg.add_reaction("7️⃣")
        elif j == "8":
            await msg.add_reaction("8️⃣")
        elif j == "9":
            await msg.add_reaction("9️⃣")
        elif j == "í":
            await msg.add_reaction("ℹ")
        elif j == "á":
            await msg.add_reaction("🅰")
        elif j == "ü":
            await msg.add_reaction("🅱")
        elif j == "ó":
            await msg.add_reaction("🅾")


@bot.command(aliases=["sag", "tts"])
async def sprich(ctx, channel_name: str = None, *, text: str = None):
    global voiceclient

    if channel_name is None and ctx.author.voice is None:
        await ctx.send("Nooooooot.")

    p_channel = None
    for ch in ctx.guild.channels:
        if str(ch).lower() == channel_name.lower():
            p_channel = bot.get_channel(ch.id)
            break

    if p_channel is None and text is not None:
        text = channel_name + " " + text
    elif p_channel is None and text is None:
        text = channel_name

    if ctx.author.voice is None and p_channel is None:
        # if *text send to unter uns without connected
        print(str(p_channel))
        await ctx.send("Ne, lass mich. Ich hab kein Bock!")
        return
    if text is None and voiceclient is not None and p_channel != voiceclient.channel:
        # Exit if not given text but connected
        await ctx.send("Reden ist Silber, Schweigen ist Gold.")
        return

    elif text is not None and text.lower() == "weisheit":
        weiseliste = ["Lieber arm dran als arm ab!",
                      "Lieber reich und gesund als arm und krank.",
                      "Wenn du ein Thema anschneidest, dann musst du es auch aufessen.",
                      "Lieber zwei Damen im Arm, als zwei Arme im Darm.",
                      "Saufen! Morgens, mittags, abends, ich will saufen!",
                      "Vertrauen ist wie Magen darm, es kommt und geht!",
                      "Lieber saufen als laufen.",
                      "Lieber Rotwein als tot sein.",
                      "Manchmal verliert man und manchmal gewinnen die anderen.",
                      "Witze über Rollstuhlfahrer sind für mich ein No-go.",
                      "Warum ein Sixpack, wenn man auch ein Fass haben kann.",
                      "Lieber Secondhand, als Armprothese.",
                      "Eine Runde Bierpong am Morgen vertreibt Kummer und Sorgen",
                      "Tim sus",
                      "Nachts ist es kälter als draußen.",
                      "Das Dorf wacht wieder auf und die Clara ist tot.",
                      "Hackfleisch kneten ist wie Tiere streicheln, nur später.",
                      "Egal wie dicht du bist, Goethe war dichter.",
                      "Besser ein Schnitzel am Teller, als beim Fritzl im Keller.",
                      "Alles im Universum ist eine Kartoffel oder keine Kartoffel.",
                      "Salzflecken auf einer Tischdecke bekommt man mit etwas Rotwein wieder heraus.",
                      "Selig sind die, die bei 'Ex oder Hurensohn' ihr Glas in einem Zug leeren.",
                      "Wer das hört ist doof!",
                      "Lieber widerlich als wieder nicht."]
        beginlst = ["Konfuzius sagte einmal: ", "Und der Jeder mit Jedem Bot sprach: ", "Wie sagt man so schön: "]
        seed(datetime.now().strftime("%d%m%Y%H%M"))
        text = choice(beginlst) + choice(weiseliste)

    if voiceclient is None:  # Not connected yet
        if p_channel is not None:
            voiceclient = await p_channel.connect()
        else:
            vc = ctx.author.voice.channel
            voiceclient = await vc.connect()
    elif p_channel is not None and voiceclient.channel != p_channel:
        await voiceclient.move_to(p_channel)
    elif ctx.author.voice is not None and ctx.author.voice.channel != voiceclient.channel:  # Not in the same channel
        await voiceclient.move_to(ctx.author.voice.channel)

    # Play TTS
    tts = gTTS(text=text, lang="de")
    if local:
        path = "audio/"
    else:
        path = "python/audio/"
    tts.save(os.path.join(path, "text.mp3"))

    try:
        # Lets play that mp3 file in the voice channel
        voiceclient.play(discord.FFmpegPCMAudio(os.path.join(path, "text.mp3")), after=lambda l: print(f"Finished playing: {text}"))

        # Lets set the volume to 1
        voiceclient.source = discord.PCMVolumeTransformer(voiceclient.source)
        voiceclient.source.volume = 1

    # Handle the exceptions that can occur
    except ClientException as e:
        await ctx.send(f"A client exception occured:\n`{e}`")
    except TypeError as e:
        await ctx.send(f"TypeError exception:\n`{e}`")
    except OpusNotLoaded as e:
        await ctx.send(f"OpusNotLoaded exception: \n`{e}`")


@bot.command(aliases=["sing"])
async def sound(ctx, channel_name: str = None, *, text: str = None):
    global voiceclient

    if channel_name is None and ctx.author.voice is None:
        await ctx.send("Nooooooot.")

    p_channel = None
    for ch in ctx.guild.channels:
        if str(ch).lower() == channel_name.lower():
            p_channel = bot.get_channel(ch.id)
            break

    if p_channel is None and text is not None:
        text = channel_name + " " + text
    elif p_channel is None and text is None:
        text = channel_name

    if ctx.author.voice is None and p_channel is None:
        # if *text send to unter uns without connected
        print(str(p_channel))
        await ctx.send("Ne, lass mich. Ich hab kein Bock!")
        return
    if text is None and voiceclient is not None and p_channel != voiceclient.channel:
        # Exit if not given text but connected
        await ctx.send("Reden ist Silber, Schweigen ist Gold.")
        return

    if voiceclient is None:  # Not connected yet
        if p_channel is not None:
            voiceclient = await p_channel.connect()
        else:
            vc = ctx.author.voice.channel
            voiceclient = await vc.connect()
    elif p_channel is not None and voiceclient.channel != p_channel:
        await voiceclient.move_to(p_channel)
    elif ctx.author.voice is not None and ctx.author.voice.channel != voiceclient.channel:  # Not in the same channel
        await voiceclient.move_to(ctx.author.voice.channel)

    text = text.lower().replace(" ", "")
    if len(text) <= 3:
        await ctx.send("Ist mir zu kurz.")
        return
    try:
        if local:
            path = "audio/"
        else:
            path = "python/audio/"
        if text in "ichhabgarnichtsgemacht":
            file = discord.FFmpegPCMAudio(os.path.join(path, 'garnichts.mp3'))
        elif text in "adler":
            file = discord.FFmpegPCMAudio(os.path.join(path, 'adler.mp3'))
        elif text in "mutterinarschgefickt":
            file = discord.FFmpegPCMAudio(os.path.join(path, 'mutter.mp3'))
        elif text in "wasbruderwassollichsagenbruder":
            file = discord.FFmpegPCMAudio(os.path.join(path, 'bruder.mp3'))
        elif text in 'hundesohn':
            file = discord.FFmpegPCMAudio(os.path.join(path, 'hundesohn.mp3'))
        elif text in 'nichtweinengirl':
            file = discord.FFmpegPCMAudio(os.path.join(path, 'girl.mp3'))
        elif text in 'merkelmachshishaauf':
            file = discord.FFmpegPCMAudio(os.path.join(path, 'shisha.mp3'))
        elif text in 'michiesistnichtskaputt':
            file = discord.FFmpegPCMAudio(os.path.join(path, 'michii.mp3'))
        elif text in 'undeinpaargeilefotzensindauchdabei':
            file = discord.FFmpegPCMAudio(os.path.join(path, 'dabei.mp3'))
        elif text in 'schwanzinmeinarsch':
            file = discord.FFmpegPCMAudio(os.path.join(path, 'arsch.mp3'))
        elif text in 'meinechickennuggetsverbrennen':
            file = discord.FFmpegPCMAudio(os.path.join(path, 'nuggets.mp3'))
        elif text in 'kapitänzurseepatentabcunddie6':
            file = discord.FFmpegPCMAudio(os.path.join(path, 'see.mp3'))
        elif text in 'montefurzmontefartmontepups':
            file = discord.FFmpegPCMAudio(os.path.join(path, 'montefart.mp3'))
        elif text in 'minecraftvillagerhmmmmmm':
            file = discord.FFmpegPCMAudio(os.path.join(path, 'villager.mp3'))
        else:
            await ctx.send("Find ich nicht, mag ich nicht.")
            return
    except FileNotFoundError:
        await ctx.send("Find ich nicht, mag ich nicht!")
        return

    try:
        # Lets play that mp3 file in the voice channel
        voiceclient.play(file, after=lambda l: print(f"Finished playing: {text}"))

        # Lets set the volume to 1
        voiceclient.source = discord.PCMVolumeTransformer(voiceclient.source)
        voiceclient.source.volume = 1

    # Handle the exceptions that can occur
    except ClientException as e:
        await ctx.send(f"A client exception occured:\n`{e}`")
    except TypeError as e:
        await ctx.send(f"TypeError exception:\n`{e}`")
    except OpusNotLoaded as e:
        await ctx.send(f"OpusNotLoaded exception: \n`{e}`")


@bot.command()
async def geh(ctx):
    # Bot leaves current voice channel
    global voiceclient
    if voiceclient is None:
        await ctx.send("Geh halt selber.")
    else:
        await voiceclient.disconnect()
        voiceclient = None


@bot.command(aliases=["büßen", "verzeihen"])
async def vergeben(ctx):
    global punished
    if not punished:
        return

    if ctx.author.id == punished[0]:
        if punished[1] <= datetime.now():
            punished = []
            await ctx.send("Deine Sünden wurden dir vergeben!")
        else:
            resttime = punished[1] - datetime.now()
            restmin = resttime.seconds // 60
            restsec = resttime.seconds % 60
            rest = ""
            if restmin >= 1:
                rest += f"{restmin} Minute{'n' if restmin != 1 else ''} und"
            await ctx.send(
                f"Du musst noch {rest} {restsec} Sekunde{'n' if restsec != 1 else ''} mit deinen Sünden leben.")
    else:
        await ctx.send("Du bist eine reine Seele. Es gibt nichts für das du büßen musst.")


@bot.command()
@commands.has_permissions(administrator=True, manage_messages=True)
async def begnadigen(ctx):
    global punished
    if punished:
        dis_name = bot.get_user(punished[0]).display_name
        await ctx.send(
            f"{dis_name} wurde vom Administrator begnadigt.")
        punished = []


@bot.command()
async def weisheit(ctx):
    # Return a random hourly intelligent message
    k = "~ Konfurzius <:konfuzius:771437774473265184>"
    m = "~ Angela Merkel <:merkel:773678321845272596>"
    b = "~ Money Boy (fly am been) :money_with_wings:"

    print([f for f in os.listdir('.')])
    if local:
        path = "files/weisheiten.txt"
    else:
        path = "python/files/weisheiten.txt"
    with open(path, "r", encoding="utf8") as file:
        weisheit_lst = file.readlines()
    for w in weisheit_lst:
        if w.startswith("#") or w == "\n" or (w[0] != "k" and w[0] != "m" and w[0] != "b"):
            weisheit_lst.remove(w)
            continue

    zitat = choice(weisheit_lst)
    person = zitat[0]

    vembed = discord.Embed(title="Die Weisheit der Stunde:", colour=discord.Colour.green())
    seed(datetime.now().strftime("%d%m%Y%H"))
    vembed.add_field(name=zitat[2:len(zitat) - 1], value=k if person == "k" else m if person == "m" else b)
    await ctx.send(embed=vembed)


@bot.command()
async def werwolf(ctx):
    # Return a random person who died in a round of werwolf
    vperson = ["die Clara", "die Clara", "die Clara", "die Clara", "die Clara", "die Clara", "die Clara", "die Clara",
               "die Clara", "die Clara", "die Clara", "der Lenny", "der Michi", "die Axelandra", "der Beni", "keiner",
               "der Josip", "der Maxi", "der Julian", "der Alex", "die Lulu"]
    await ctx.send("Das Dorf schläft ein!")
    await asyncio.sleep(randrange(5, 10))
    await ctx.send("Das Dorf wacht wieder auf und %s ist tot!" % (choice(vperson)))


@bot.command(aliases=["mc"])
async def minecraft(ctx, mode: str = "", *, arg: str = None):
    async with ctx.channel.typing():
        mcserver = MinecraftServer.lookup(mc_ip)
        motd = " +--+ Mixi Miners Remastered \u26CF +--+"
        if local:
            path = "files/server-icon.png"
        else:
            path = "python/files/server-icon.png"
        icon = discord.File(path, filename="server-icon.png")  # Local file as attachment
        embed = discord.Embed(description=motd,
                              colour=discord.Colour.dark_green())
        embed.set_author(name="Mixi Miners", icon_url="attachment://server-icon.png")
        if ctx.channel.name == "minecraft":
            embed.add_field(name="IP-Adresse", value=mc_ip, inline=False)
        if mode.lower() == "status":  # Get number of online players
            try:
                query = mcserver.query()
                players = "\n".join([str(x) for x in query.players.names])  # Format names of online players
                if not players:  # If none online
                    players = "Herobrine"

                embed.add_field(name=f"{query.players.online} Spieler online", value=players, inline=False)
                await ctx.send(file=icon, embed=embed)
            except ConnectionRefusedError:  # Server cannot be reached
                embed.add_field(name="Der Server ist gerade offline", value=":(", inline=False)
                await ctx.send(file=icon, embed=embed)
        elif mode.lower() == "ping":
            try:
                mcstatus = mcserver.status()
                embed.add_field(name="Ping", value=f"{str(mcstatus.latency).replace('.',',')} ms", inline=False)
                await ctx.send(file=icon, embed=embed)
            except ConnectionRefusedError:
                embed.add_field(name="Der Server ist gerade offline", value=":(", inline=False)
                await ctx.send(file=icon, embed=embed)
        elif mode.lower() == "start":
            try:
                mcserver.status()
                await ctx.send("Der Server läuft doch schon, du Trottel.")
            except:
                await ctx.send("<@!383717762549153802>, bitte starte den Minecraft Server!")
        # elif mode.lower() == "stats":
        else:
            await ctx.send("Bitte gib einen Modus an. Verfügbare Modi: 'status', 'start', 'ping'.\n"
                           "Verwendung: 'bitte minecraft <modus>")


# Mixi exclusive Commands ------------------------------------

@bot.command(aliases=["verstecke"])
@commands.has_role("[VIP] Mixi")
async def disguise(ctx, channel_id: str, *, msg: str = None):
    # send a secret message disguising as the bot
    if msg is None:
        await ctx.message.delete()
        await ctx.send(channel_id)
    else:
        await ctx.message.delete()
        channel = getchannel(channel_id)
        if channel is None:
            await ctx.send(channel_id + " " + msg)
        elif channel.type == "voice":
            return
        else:
            await channel.send(msg)


@bot.command()
@commands.has_role("[VIP] Mixi")
async def imp(ctx, title: str = "<Title>", desc: str = None, head: str = None, value="<Main>"):
    # send a secret embeded message disguising as the bot
    await ctx.message.delete()
    vembed = discord.Embed(title=title, description=desc, colour=discord.Colour.red())
    if head:
        vembed.add_field(name=head, value=value, inline=False)
    await ctx.send(embed=vembed)


@bot.command()
@commands.has_role("[VIP] Mixi")
async def status(ctx, *, botstatus: str = None):
    # set status of bot (default: os.environ["DEFAULT_STATUS"])
    await ctx.message.delete()
    if botstatus is None:
        botstatus = default_status
    else:
        os.environ['DEFAULT_STATUS'] = botstatus
    await bot.change_presence(activity=discord.Game(name=botstatus))


# Hidden Admin Commands ------------------------------------

@bot.command(aliases=["clean", "aufräumen", "delete"])
@commands.has_permissions(administrator=True, manage_messages=True)
async def clear(ctx, amount: int = 1, *, safe: str = None):
    # Delete certain amount of messages (bulk delete)
    dmsg = []
    issafe = safe is not None and safe.lower() == "ich bin sicher! " + str(ctx.channel).lower()
    if amount > 3 and not issafe and str(ctx.channel) != "bot-test":
        msg = await ctx.send("You can't delete that many messages in a public channel, "
                             "if you don't confirm your clear with 'Ich bin sicher! <channel-name>'")
        timedmsg.append([msg, datetime.now() + timedelta(seconds=10)])
        return
    if amount < 1:
        await ctx.send("haha. lustig.")
        return
    elif amount > 99:
        amount = 99
    async for msg in ctx.history(limit=amount + 1):
        if msg.created_at + timedelta(days=12 if issafe else 1) > datetime.now():
            dmsg.append(msg)
    await ctx.channel.delete_messages(dmsg)


@bot.command(aliases=["oldclear", "olddelete", "bulkdelete"])
@commands.has_permissions(administrator=True)
async def bulkclear(ctx, amount: int = 1, *, safe: str = None):
    # Delete certain amount of messages (works with old messages)
    issafe = safe is not None and safe.lower() == "ich bin sicher! " + str(ctx.channel).lower()
    if amount > 3 and not issafe and str(ctx.channel) != "bot-test":
        msg = await ctx.send("You can't delete that many messages in a public channel, "
                             "if you don't confirm your clear with 'Ich bin sicher! <channel-name>'")
        timedmsg.append([msg, datetime.now() + timedelta(seconds=10)])
        return
    if amount < 1:
        await ctx.send("haha. lustig.")
        return
    async for msg in ctx.history(limit=amount + 1):
        await msg.delete()


@bot.command(aliases=["quit", "exit"])
@commands.has_permissions(administrator=True, manage_messages=True)
async def quitbot(ctx):
    # Quit bot
    await ctx.send("Bot geht jetzt schlafen. Gute Nacht!")
    exit()


@bot.command(aliases=["test"])
async def version(ctx):
    # Version des Bots ausgeben
    await ctx.send(f"{bot.user.name} | by Beni#5598 | Version: {jmjversion}\n"
                   f"Quellkot: https://github.com/no-pizza-hawaii/jmjbot")


# End
always_active.start()
bot.run(TOKEN)
