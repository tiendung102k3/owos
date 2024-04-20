import numpy as np
import cv2

from ultralytics import YOLO
from re import finditer, MULTILINE
from asyncio import sleep
from random import randint
from discord.ext import tasks
from json import loads

from src.logger import logger


class Huntbot:
    def __init__(self, client):
        self.client = client
        self.data = client.data
        self.model = YOLO("src/huntbot.pt")

    async def __preprocess(self, img: bytes, grayscale: bool = False) -> cv2.typing.MatLike:
        img = np.frombuffer(img, np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)
        # Create A Mask To Filter Out Some Of The Stripes' Pixels
        stripe_min = np.array([1, 1, 1], np.uint8)
        stripe_max = np.array([255, 255, 255], np.uint8)

        HSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(HSV, stripe_min, stripe_max)

        # Exclude The Color Of The Letters
        letter_color_min = np.array([106, 189, 255], np.uint8)
        letter_color_max = letter_color_min  # The Letters Only Have One Color

        mask_to_exclude = cv2.inRange(
            HSV, letter_color_min, letter_color_max)

        mask_to_keep = cv2.bitwise_not(mask_to_exclude)

        # Combine The Stripes' Mask And The Letters'
        final_mask = cv2.bitwise_and(mask, mask_to_keep)
        img[final_mask > 0] = [0, 0, 0]

        # Calculate The Histogram of Colors In The Remaining Image
        histogram = cv2.calcHist([img], [0, 1, 2], None, [
            256, 256, 256], [0, 256, 0, 256, 0, 256])

        # Find The Color With The Least Occurrence (Left-over Noise Pixels)
        min_color = np.unravel_index(np.argmin(histogram), histogram.shape)

        # And Removing Them
        min_color = np.array(min_color)
        img[np.all(img == min_color, axis=-1)] = [0, 0, 0]

        if grayscale:
            # Apply Histogram Equalization to The Grayscale Image For Contrast Enhancement
            img = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        return img

    async def __predict(self, img: cv2.typing.MatLike) -> tuple:
        results = self.model.predict(
            img,
            conf=0.6,
            iou=0.1,
            max_det=5,
            imgsz=640,
            agnostic_nms=True,
            save=True,
            exist_ok=True,
            show_boxes=False
        )

        results = loads(results[0].tojson())

        results = sorted(
            [
                (result["name"], result["box"]["x1"])
                for result in results
            ], key=lambda x: x[1])

        print(results)
        return "".join([result[0] for result in results])

    @tasks.loop(seconds=25)
    async def start(self) -> None:
        async with self.client.can_run:
            name = self.client.get_guild(self.data.guild).me.display_name
            channel = self.client.get_channel(self.data.channel)

            await channel.send(f"owo autohunt {self.data.huntbot}")

            try:
                captcha = await self.client.wait_for(
                    "message", check=lambda m:
                        m.channel.id == self.data.channel
                        and name in m.content
                        and "Here is" in m.content
                        or "BACK IN" in m.content
                        or "BACK WITH" in m.content,
                    timeout=6)
            except:
                logger.critical("Couldn't Autohunt")
                captcha = None

            if captcha and "Here is" in captcha.content:
                captcha_img = await captcha.attachments[0].read()

                answer = await self.__predict(await self.__preprocess(captcha_img))

                for _ in range(2):
                    await channel.send(f"owo autohunt {self.data.huntbot} {answer}")

                    try:
                        verify = await self.client.wait_for(
                            "message", check=lambda m:
                            m.channel.id == self.data.channel
                            and name in m.content
                            and "BEEP BOOP" in m.content,
                            timeout=6)
                        break
                    except TimeoutError:
                        answer = await self.__predict(
                            await self.__preprocess(captcha_img, grayscale=True)
                        )
                        verify = False

                if verify:
                    logger.info("Autohunt Succeeded!")
                    self.start.change_interval(seconds=20)
                else:
                    logger.critical("Autohunt Failed!")
                    self.start.change_interval(minutes=10, seconds=15)

            elif captcha and "STILL HUNTING" in captcha.content:
                regex = r"(?<=I WILL BE BACK IN )\d+(?=M)|(\d{1,2}\.\d{1,2}%)|(ANIMALS CAPTURED|■{20}□{20})(?<=\| ).*?(?=\sDONE)|(?<=\| ).*?(?=\sCAPTURED)|(?<=\[).*?(?=\])"
                matches = [match.group() for match in finditer(
                    regex, captcha.content, MULTILINE)]

                print(matches)
                logger.warning(
                    f"Autohunt Captured: {matches[1]} | Done After: {matches[2]} ({matches[0]}) ")
            elif captcha and "I AM BACK WITH" in captcha.content:
                logger.info("Autohunt Completed!")

            await sleep(randint(3, 6))

    @start.before_loop
    async def before_start(self):
        await self.client.wait_until_ready()
