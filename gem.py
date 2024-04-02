from asyncio import TimeoutError
from re import findall

from src.logger import logger


class Gem:

    def __classify_gems(self, inv):
        gems = [
            [gem for gem in inv
             if range[0] < gem < range[1]
             ]
            for range in
            [(50, 58), (64, 72), (71, 79), (79, 86)]
        ]  # Hunting, Empowering, Lucky and Special Gem Type Respectively

        list_rarity = [
            [51, 65, 72, 79],  # Common Gems
            [52, 66, 73, 80],  # Uncommon Gems
            [53, 67, 74, 81],  # Rare Gems
            [54, 68, 75, 82],  # Epic Gems
            [55, 69, 76, 83],  # Mythical Gems
            [56, 70, 77, 84],  # Legendary Gems
            [57, 71, 78, 85],  # Fabled Gems
        ]

        def classify_rarity(gem):
            for index, rarity in enumerate(list_rarity):
                if gem in rarity:
                    return (index, gem)

        for index, type in enumerate(gems):
            gems[index] = list(map(classify_rarity, type))

        print(gems)

    async def fetch_gem(self):
        await self.get_channel(self.data.channel).send("owo inv")

        name = self.get_guild(self.data.guild).me.display_name

        try:
            inv = await self.wait_for("message",
                                      check=lambda m: m.author.id == self.owoid
                                      and name in m.content
                                      and "Inv" in m.content,
                                      timeout=6)

        except TimeoutError:
            logger.critical("Couldn't Fetch Inventory")

        inv = findall(r"`(.*?)`", inv.content)
        inv = [int(item) for item in inv if item.isnumeric()]

        print(f"Inv: {inv}")
        self.__classify_gems(inv)

        return inv
