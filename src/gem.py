from discord import Client
from asyncio import TimeoutError, sleep
from random import randint
from re import findall, finditer, MULTILINE
from src.logger import logger
from src.data import Data


class Gem:
    def __init__(self, client):
        self.client: Client = client
        self.data: Data = client.data

    def __available(self, gems):
        available = {}

        for index, type in enumerate(gems):
            if type:
                if index == 0:
                    available["gem1"] = type
                elif index == 1:
                    available["gem3"] = type
                elif index == 2:
                    available["gem4"] = type
                else:
                    if self.data.gem["star"]:
                        available["star"] = type

        self.available = available

    def __classify_gems(self, inv):
        gems = [
            sorted(
                [gem for gem in inv
                 if range[0] < gem < range[1]
                 ]
            )
            for range in
            [(50, 58), (64, 72), (71, 79), (79, 86)]
        ]  # Hunting, Empowering, Lucky and Special Gem Type Respectively

        return gems

    async def __fetch_gem(self):
        await self.client.get_channel(self.data.channel).send("owo inv")

        name = self.client.get_guild(self.data.guild).me.display_name

        try:
            inv = await self.client.wait_for("message",
                                             check=lambda m: m.author.id == self.client.owoid
                                             and name in m.content
                                             and "Inv" in m.content,
                                             timeout=6)
            inv = findall(r"`(.*?)`", inv.content)
            inv = [int(item) for item in inv if item.isnumeric()]
        except TimeoutError:
            logger.critical("Couldn't Fetch Inventory")
            self.available = None
            await sleep(randint(4, 6))
            await self.__fetch_gem()

        return self.__classify_gems(inv)

    async def __use_gem(self, rarity, gems=0):
        use = []

        if gems == 0:
            for type in self.available.values():
                if rarity == "average":
                    avg = len(type) / 2
                    avg = int((avg - .5)) if len(type) % 2 != 0 else int(avg)

                use.append(
                    type[rarity] if rarity != "average" else type[avg]
                )
        else:
            for gem in gems:
                if rarity == "average":
                    avg = len(type) / 2
                    avg = int(
                        (avg - .5)) if len(type) % 2 != 0 else int(avg)

                use.append(
                    self.available[gem][rarity] if rarity != "average" else self.available[gem][avg]
                )

        await self.client.get_channel(self.data.channel).send(
            f"owo use {' '.join(str(gem) for gem in use)}"
        )

        await sleep(randint(6, 8))
        gems = await self.__fetch_gem()
        self.__available(gems)

    async def detect_gem(self, message, rarity=-1):
        if not self.client.hunt.is_running():
            return

        name = self.client.get_guild(self.data.guild).me.display_name
        if not (message.author.id == self.client.owoid
                and message.channel.id == self.data.channel
                and name in message.content
                and "🌱" in message.content):
            return

        if not getattr(self, "available", None):
            inv = await self.__fetch_gem()
            self.__available(inv)
            await sleep(randint(4, 6))
            print(f"avail: {self.available}")

        regex = r"(gem\d|star):\d+>`\[(\d+)"

        matches = [
            match.groups()
            for match in finditer(regex, message.content, MULTILINE)
        ]

        use = ["gem1", "gem3", "gem4", "star"]

        if len(matches) == 0 and len(self.available) == 4:
            # print(message.content)
            # print(matches)
            # print(self.available)
            await self.__use_gem(rarity)
            await sleep(randint(4, 6))
            return

        for name, count in matches:
            if int(count) > 0:
                use.remove(name)

        for gem in use:
            if gem not in self.available:
                use.remove(gem)

        # print(f"matches: {matches}")
        # print(f"Use {use}")

        if use:
            await self.__use_gem(rarity, use)
            await sleep(randint(4, 6))
