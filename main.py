import discord
import asyncio
import logging
import youtube_dl
from discord.ext import commands
from random import choice


def log_setup():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)


log_setup()
ytdl_format_options = {
    'format': 'bestaudio',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(
            filename, **ffmpeg_options, executable="D:/Workspace/Background Bro/FFMPEG/bin/ffmpeg.exe"
        ), data=data)


class Music(commands.Cog):
    def __init__(self, bot_in):
        self.bot = bot_in

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """Joins a voice channel"""

        if channel is None:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                print("You didn't say which channel, bro.")
                return await ctx.send("You didn't say which channel, bro.")
        else:
            print(f'Alright, joining #{channel}')
            await ctx.send(f'Alright, joining #{channel}')
            if ctx.voice_client is not None:
                return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""

        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print('Look at this player error: %s' % e) if e else None)

        await ctx.send(f'You got it. Now playing:\n```{query}```')

    @commands.command()
    async def yt(self, ctx, *, url):
        """Plays from a url (almost anything youtube_dl supports)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print('Look at this player error: %s' % e) if e else None)

        await ctx.send(f'You got it. Now playing:\n```{player.title}```')

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Look at this player error: %s' % e) if e else None)

        await ctx.send(f'You got it. Now playing:\n```{player.title}```')

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("I'm not connected to a voice channel, bro.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        async with ctx.channel.typing():
            await ctx.send("Alright then. See you around.")
        await ctx.voice_client.disconnect()

    @play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You're not connected to a voice channel, bro.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


client = commands.Bot(command_prefix=commands.when_mentioned_or("... "))


@client.event
async def on_ready():
    print(f'Hey there. Logged in as {client.user}')


@client.command()
async def bro(ctx):
    await ctx.send('Hey there, bro. Let me get set up, then we can party.')


@client.command()
async def will(ctx, *, msg):
    if msg == "Penguin get a new laptop?":
        penguin_laptop = ["Honestly I don't know bro",
                          "He's the only one who can answer that.",
                          "No clue, bro",
                          "I dunno, man.",
                          "I don't know",
                          "Don't ask me, bro. Ask him.",
                          "no clue",
                          "Who knows?"
                          "Is there really a chance of that?",
                          "Honestly I have no idea",
                          "Not my place to say"]
        await ctx.send("Uh...")
        async with ctx.channel.typing():
            await asyncio.sleep(1)
            await ctx.send(choice(penguin_laptop))


client.add_cog(Music(client))
with open('Token.txt') as t:
    client.run(t.read())

if __name__ == "__main__":
    print("Hello, this is the Background Bro's script file")
