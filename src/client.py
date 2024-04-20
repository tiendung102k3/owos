import discord
from discord.ext import tasks
from functools import partial
from asyncio import Lock, sleep
from typing import Union
from random import randint

from src.logger import logger
from src.captcha_handler import is_captcha, solve_captcha
from data2 import Data
from gem import Gem


class TempClient(discord.Client):
    async def on_ready(self):
        await self.close()


class Client(discord.Client, Gem):
    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Gem().__init__()
        self.data = data
        self.owoid = 408785106942164992
        self.can_run = Lock()

    async def setup_hook(self):
        await self.runner()

    async def on_ready(self):
        logger.warning(f"Logged in as {self.user}")

    async def on_message(self, message):
        if is_captcha(self.user, message):
            logger.critical("Captcha Detected!")

            if self.data.solve:
                logger.info("Attempting to Solve Captcha...")
                solve_captcha(self.data.token)

    async def on_guild_channel_update(self, before, after):
        if (after.id == self.data.channel
                and not after.permissions_for(after.guild.me).use_application_commands):
            setattr(self, "cmds", {})

    async def runner(self, state: bool = True) -> None:
        tasks = [
            self.hunt,
            self.battle,
            self.gem
        ]

        for task in tasks:
            try:
                task.start() if state else task.cancel()
            except RuntimeError:
                ...

    async def slash_cmd(self) -> Union[dict[str, discord.SlashCommand], dict]:
        if getattr(self, "cmds", None):
            return self.cmds
        channel = self.get_channel(self.data.channel)

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

    @tasks.loop(seconds=20)
    async def hunt(self) -> None:
        async with self.can_run:
            slash_cmds = await self.slash_cmd()

            await slash_cmds.get("hunt",
                                 partial(
                                     self.get_channel(
                                         self.data.channel).send,
                                     "owo hunt"
                                 )
                                 )()

            await sleep(randint(1, 5))

    @tasks.loop(seconds=22)
    async def battle(self) -> None:
        async with self.can_run:
            slash_cmds = await self.slash_cmd()

            await slash_cmds.get("battle",
                                 partial(
                                     self.get_channel(self.data.channel).send,
                                     "owo battle"
                                 )
                                 )()

            await (sleep(randint(1, 5)))

    @tasks.loop(seconds=120)
    async def gem(self) -> None:
        async with self.can_run:
            inv = await self.fetch_gem()

    @hunt.before_loop
    async def before_hunt(self):
        await self.wait_until_ready()

    @battle.before_loop
    async def before_battle(self):
        await self.wait_until_ready()

    @gem.before_loop
    async def before_gem(self):
        await self.wait_until_ready()


