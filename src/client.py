import discord
from discord.ext import tasks
from functools import partial
from asyncio import Lock, sleep, new_event_loop, set_event_loop
from random import randint
from re import finditer, MULTILINE
from threading import Thread
from sys import exc_info

from src.logger import logger
from src.captcha_handler import is_captcha, solve_captcha
from src.huntbot import Huntbot
from src.data import Data
from src.gem import Gem


class TempClient(discord.Client):
    async def on_ready(self):
        await self.close()


class Client(discord.Client):
    """
    The Class Resposible For The Client Behavior

    :param data: Class Data (src.data)
    :param *args: Positional Arguments for discord.Client (Optional)
    :param **kwargs: Keyword Arguments for discord.Client (Optional)
    """

    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data: Data = data
        self.owoid: int = 408785106942164992
        self.gem: Gem = Gem(self)
        self.huntbot: Huntbot = Huntbot(self)
        self.can_run: Lock = Lock()

    async def setup_hook(self):
        await self.scheduler()

    async def on_ready(self):
        logger.warning(f"Logged in as {self.user}")

    async def on_message(self, message: discord.Message):
        if is_captcha(self.user, message):
            logger.critical("Captcha Detected!")

            await self.scheduler(False)

            if self.data.solve:
                logger.info("Attempting to Solve Captcha...")
                await solve_captcha(self.data.token)

        if self.data.gem["enabled"]:
            async with self.can_run:
                await self.gem.detect_gem(message)

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        # Get Battle Result
        name: str = self.get_guild(self.data.guild).me.display_name

        if (after.author.id == self.owoid
            and after.channel.id == self.data.channel
            and (embeds := after.embeds)
            and name in embeds[0].author.name
                and " Your team gained" in (result := embeds[0].footer.text)):

            partial(
                logger.info if "won" in result else logger.warning,
                result
            )()

    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        if (after.id == self.data.channel
                and not after.permissions_for(after.guild.me).use_application_commands):
            setattr(self, "cmds", {})

    async def scheduler(self, state: bool = True) -> None:
        methods: list[tasks.Loop] = [
            self.hunt,
            self.battle,
            self.huntbot.start,
            self.claim_daily
        ]

        for task in methods:
            try:
                task.start() if state else task.cancel()
            except RuntimeError:
                continue

    async def slash_cmd(self) -> dict[str, discord.SlashCommand] | dict:
        if getattr(self, "cmds", None):
            return self.cmds

        channel: discord.TextChannel = self.get_channel(self.data.channel)

        if channel.permissions_for(channel.guild.me).use_application_commands:
            cmds = {
                cmd.name: cmd
                for cmd in
                await channel.application_commands()
                if cmd.application_id == self.owoid
            }

            self.cmds = cmds

            return cmds

        return {}

    @tasks.loop(seconds=25)
    async def hunt(self) -> None:
        async with self.can_run:
            slash_cmds: dict[str, discord.SlashCommand] = await self.slash_cmd()
            channel: discord.TextChannel = self.get_channel(self.data.channel)
            name: str = channel.guild.me.display_name

            try:
                await slash_cmds.get("hunt",
                                     partial(
                                         channel.send,
                                         "owo hunt"
                                     )
                                     )()
            except discord.errors.InvalidData:
                ...

            try:
                msg: discord.Message = await self.wait_for(
                    "message",
                    check=lambda m:
                        m.channel.id == self.data.channel
                        and (name in m.content and "🌱" in m.content),
                    timeout=3
                )
            except TimeoutError:
                logger.info("Hunt (+?xp)")
                return

            regex: str = r"\b\d+[a-zA-Z]{2}\b"
            xp: str = list(finditer(regex, msg.content, MULTILINE))[0].group()
            logger.info(f"Hunt (+{xp})")

            await sleep(randint(3, 6))

    @tasks.loop(seconds=32)
    async def battle(self) -> None:
        async with self.can_run:
            slash_cmds: dict[str, discord.SlashCommand] = await self.slash_cmd()

            try:
                await slash_cmds.get("battle",
                                     partial(
                                         self.get_channel(
                                             self.data.channel).send,
                                         "owo battle"
                                     )
                                     )()
            except discord.errors.InvalidData:
                ...

            await sleep(randint(3, 6))

    @tasks.loop(minutes=2)
    async def claim_daily(self) -> None:
        async with self.can_run:
            channel: discord.TextChannel = self.get_channel(self.data.channel)
            name: str = channel.guild.me.display_name

            await channel.send("owo daily")

            try:
                msg: discord.Message = await self.wait_for(
                    "message",
                    check=lambda m:
                        m.channel.id == channel.id
                        and name in m.content
                        and ("Here is your daily" in m.content
                             or "You need to wait" in m.content),
                    timeout=6
                )
            except TimeoutError:
                msg = None
                logger.critical("Couldn't Claim Daily")

            if msg and "Here is your daily" in msg.content:
                regex: str = r"(\d+ daily streak)|(\d+ Cowoncy)|((?<=: )[^:]+)"

                matches: list[str] = [match.group() for match in finditer(
                    regex, msg.content, MULTILINE)]

                logger.info(
                    f"""
                    Claimed Daily ({matches[1]})!
                    Received: {matches[0]}
                    Next Daily: {matches[2]}
                    """
                )

                time: list[int] = [int(t[:-1]) for t in matches[2].split(" ")]

                self.claim_daily.change_interval(
                    hours=time[0],
                    minutes=time[1] + 1,
                    seconds=time[2]
                )
            elif msg and "You need to wait" in msg.content:
                regex: str = r"\d+"
                matches: list[int] = [
                    int(match.group()) for match in finditer(
                        regex, msg.content)
                ]

                # print(matches)
                self.claim_daily.change_interval(
                    hours=matches[0],
                    minutes=matches[1] + 1,
                    seconds=matches[2])
            else:
                logger.critical("Couldn't Claim Daily")
            await sleep(randint(3, 6))

    @hunt.before_loop
    async def before_hunt(self):
        await self.wait_until_ready()

    @battle.before_loop
    async def before_battle(self):
        await self.wait_until_ready()

    @claim_daily.before_loop
    async def before_claim_daily(self):
        if not self.data.daily:
            self.claim_daily.cancel()
        await self.wait_until_ready()


class CreateThread(Thread):
    """
    Initialize A Thread of class Client to Run Concurrently with Threading Module

    :param client: class Client (src.client), an instance of discord.Client"""

    def __init__(self, client: Client) -> None:
        super(CreateThread, self).__init__()
        self.client: Client = client
        self.daemon: bool = True

    async def start_bot(self) -> None:
        await self.client.start(self.client.data.token)

    async def stop(self) -> None:
        try:
            await self.client.scheduler(False)
            await self.client.close()
        except:
            ...  # Stopped Regardless of Exceptions

    def run(self):
        loop = new_event_loop()
        set_event_loop(loop)
        loop.run_until_complete(self.start_bot())
