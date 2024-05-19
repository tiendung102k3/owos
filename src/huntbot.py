import cv2

import discord
from discord.ext import tasks

from ultralytics import YOLO
from ultralytics.engine.results import Results

from numpy import frombuffer, array, uint8
from re import finditer, MULTILINE
from asyncio import sleep
from random import randint
from json import loads

from src.logger import logger
from src.data import Data


class Huntbot:
    def __init__(self, client):
        self.client: discord.Client = client
        self.data: Data = client.data
        self.model = YOLO("src/huntbot.pt")

    async def __preprocess(self, img: bytes) -> cv2.typing.MatLike:
        img = frombuffer(img, uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)
        # Create A Mask To Filter Out Some Of The Stripes' Pixels
        stripe_min = array([1, 1, 1], uint8)
        stripe_max = array([255, 255, 255], uint8)

        HSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(HSV, stripe_min, stripe_max)

        # Exclude The Color Of The Letters
        letter_color_min = array([106, 189, 255], uint8)
        letter_color_max = letter_color_min  # The Letters Only Have One Color

        mask_to_exclude = cv2.inRange(
            HSV, letter_color_min, letter_color_max)

        mask_to_keep = cv2.bitwise_not(mask_to_exclude)

        # Combine The Stripes' Mask And The Letters'
        final_mask = cv2.bitwise_and(mask, mask_to_keep)
        img[final_mask > 0] = [0, 0, 0]

        # Apply Histogram Equalization to The Grayscale Image For Contrast Enhancement
        img = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        return img

    async def __predict(self, img: cv2.typing.MatLike) -> tuple:
        results: Results = self.model.predict(
            img,
            conf=0.0,
            iou=0.1,
            max_det=5,
            imgsz=640,
            agnostic_nms=True,
            save=True,
            show_boxes=False,
        )

        results: dict = loads(results[0].tojson())

        results: list = sorted(
            [
                (result["name"], result["box"]["x1"])
                for result in results
            ], key=lambda x: x[1])

        print(results)
        return "".join([result[0] for result in results])

    @tasks.loop(seconds=30)
    async def start(self) -> None:
        async with self.client.can_run:
            name: str = self.client.get_guild(self.data.guild).me.display_name
            channel: discord.TextChannel = self.client.get_channel(
                self.data.channel)

            await channel.send(f"owo autohunt {self.data.huntbot}")

            try:
                captcha: discord.Message = await self.client.wait_for(
                    "message", check=lambda m:
                        m.channel.id == self.data.channel
                        and name in m.content
                        and "Here is" in m.content
                        or "BACK IN" in m.content
                        or "BACK WITH" in m.content,
                    timeout=6)
            except:
                logger.critical("Couldn't Autohunt")
            else:
                if "Here is" in captcha.content:
                    captcha_img: bytes = await captcha.attachments[0].read()

                    answer: str = await self.__predict(await self.__preprocess(captcha_img))

                    await channel.send(f"owo autohunt {self.data.huntbot} {answer}")

                    try:
                        await self.client.wait_for(
                            "message", check=lambda m:
                            m.channel.id == self.data.channel
                            and name in m.content
                            and "BEEP BOOP" in m.content,
                            timeout=6)
                    except TimeoutError:
                        logger.critical("Autohunt Failed!")
                        self.start.change_interval(minutes=10, seconds=15)
                    else:
                        logger.info("Autohunt Succeeded!")
                        self.start.change_interval(seconds=20)
                elif "STILL HUNTING" in captcha.content:
                    regex = r"(?<=I WILL BE BACK IN )(\d+)(?=M)|(?:\d*(?:\.\d+)?)%|(ANIMALS CAPTURED|■{20}□{20})(?<=\| ).*?(?=\sDONE)|(?<=\| ).*?(?=\sCAPTURED)|(?<=\[).*?(?=\])"
                    matches: list = [match.group() for match in finditer(
                        regex, captcha.content, MULTILINE)]

                    print(matches)
                    logger.warning(
                        f"Autohunt Captured: {matches[2]} | Done After: {matches[0]} minutes ({matches[1]})\n{matches[3]}")

                    self.start.change_interval(minutes=int(matches[0]))
                elif "I AM BACK WITH" in captcha.content:
                    logger.info("Autohunt Completed!")

            await sleep(randint(3, 6))

    @start.before_loop
    async def before_start(self):
        if not self.data.huntbot:
            self.start.cancel()
        await self.client.wait_until_ready()
