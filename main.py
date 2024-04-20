    import logging

from nicegui import app, ui
from discord.errors import LoginFailure
from discord import TextChannel

from src.data import Data
from src.client import Client, TempClient
from src.logger import logger

from typing import Type
from re import search
from asyncio import sleep
from functools import partial
from threading import Thread

app.add_static_files("/static", "static")

ui.add_head_html(
    """ 
                    <link rel='stylesheet' type="text/css" href="./static/styles.css">
                   
                    <link rel="preconnect" href="https://fonts.googleapis.com">
                    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                    <link href="https://fonts.googleapis.com/css2?family=Prompt:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap" rel="stylesheet">
                    
                    <link
                      rel="stylesheet"
                      href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"
                      
                     
  />
                 """
)


class GUI:
    def __init__(self):
        self.data: Type["Data"] = Data()
        self.client = None

    async def load_account(self, token: str) -> TempClient:
        print(token)

        if not search(r"[\w-]{24}\.[\w-]{6}\.[\w-]{38}", token):
            raise LoginFailure

        ui.notify("Logging In...", type="positive")
        client = TempClient(max_messages=None, guild_subscriptions=False)
        await client.start(token)

        return client

    def start_bot(self, account: str) -> None:
        data = self.data.load(account)
        self.client = Client(data, max_messsages=1500)
        client_thread = Thread(
            target=partial(
                self.client.run, data.token)
        )
        client_thread.start()

    @ui.refreshable
    def info_account(self, client=None):
        with ui.card().classes("animate__animated animate__flipInX q-card-info"):
            if client:
                with ui.card_section().classes("p-0"):
                    with ui.element("div").classes("info-container"):
                        with ui.element("div").classes("user-info"):
                            with ui.avatar(size="150px", color="grey"):
                                ui.image(client.user.display_avatar.url)
                            ui.label(client.user.name).classes(
                                "q-username text-h4")
                        ui.element("div").classes("seperator")
                        with ui.element("div").classes("user-status"):
                            ui.label(f"User ID: {client.user.id}")
                            ui.label(f"Email: {client.user.email}")
                            ui.label(f"MFA Enabled: {client.user.mfa_enabled}")
                            ui.label(f"Created At: {
                                client.user.created_at.strftime("%m/%d/%Y, %H:%M:%S")}")
                            ui.label(
                                f"Guild: {client.get_guild(self.data.guild).name}")
                            ui.label(
                                f"Channel: {client.get_channel(self.data.channel).name}")
                        ui.element("div").classes("seperator")
                        with ui.element("div").classes("user-status"):
                            for _ in range(5):
                                ui.label("user status 2")

                        ui.button(
                            "Start Selfbot!",
                            on_click=partial(
                                self.start_bot, client.user.name
                            )).props('outline')

            else:
                ui.label("No Account Selected").classes('w-full text-h4')
                ui.image('./static/lf.gif').classes('looking-img')

    @ui.refreshable
    def show_account(self):
        async def load_event(account):
            self.data.load(account)
            client = await self.load_account(self.data.token)
            self.info_account.refresh(client)

        async def remove_event(account):
            self.data.remove(account)

            if self.data.name == account:
                print("YES?")
                self.info_account.refresh(None)

            ui.notify("Account Removed!", type="positive")
            self.show_account.refresh()

        for account in self.data.get_account():
            with ui.card().classes("q-card-select"):
                ui.label(account).classes("w-full")
                with ui.card_section().classes("btn-section p-0"):
                    ui.button(
                        text="Select",
                        icon="send",
                        on_click=partial(load_event, account),
                    ).props("outline")

                    ui.button(
                        text="Remove",
                        icon="delete",
                        on_click=partial(remove_event, account),
                    ).props("outline")

    def main(self):
        with ui.tabs().classes("main-tabs") as tabs:
            with ui.element("div").classes("tabs-box animate__animated  animate__bounceIn"):
                ui.tab("h", label="Home", icon="home").classes("tab-item")
                ui.tab("a", label="Settings",
                       icon="settings").classes("tab-item")

        with ui.tab_panels(tabs, value="h").classes("w-full"):
            with ui.tab_panel("h") as tab:
                with ui.element("div").classes("tab-panel-content"):
                    ui.label("SELECT ACCOUNT").classes("tab-panel-title")

                with ui.element("div").classes("cards-layout"):
                    self.show_account()
                    ui.button(icon="add", on_click=lambda: self.new_account()
                              ).classes("add-button")

                with ui.element("div").classes("tab-panel-content"):
                    ui.label("ACCOUNT INFO").classes("tab-panel-title")

                with ui.element("div").classes("cards-layout"):
                    self.info_account()

                with ui.element("div").classes("cards-layout"):
                    log = ui.log().classes('w-full h-40')
                    log.bind_visibility_from(self.data, "name")
                    logger.addHandler(LogElementHandler(log))
                    logger.setLevel(logging.INFO)

            with ui.tab_panel("a"):
                with ui.element("div").classes("tab-panel-content"):
                    ui.label("SETTINGS").classes("tab-panel-title")

    def new_account(self):
        (
            token,
            channel,
            guild,
            gem,
            pray,
            exp,
            url,
            ping,
            ping_self,
            commands,
            daily,
            sell,
            solve,
            huntbot
        ) = (None,) * 14

        def create_data(client: TempClient, run=False):
            data = {
                "token": token.value,
                "guild": guild.value,
                "channel": channel.value,
                "gem": gem.value,
                "pray": pray.value,
                "exp": exp.value,
                "webhook": {
                    "url": url.value,
                    "ping": (
                        [
                            int(ping.value) if ping.value else None,
                            client.user.id if ping_self.value else None,
                        ]
                        if (ping.value or ping_self.value)
                        else None
                    ),
                },
                "commands": commands.value if commands.value else None,
                "daily": daily.value,
                "sell": (
                    sell.value if (not sell.value) or (
                        not "All" in sell.value) else "All"
                ),
                "solve": solve.value,
                "huntbot": huntbot.value
            }

            ui.notify(str(data), type="positive")
            self.data = self.data.save(client.user.name, data)
            self.show_account.refresh()
            dialog.close()

            if run:
                self.start_bot(client.user.name)
                self.info_account.refresh(client)

        async def get_guild(button):
            if stepper.default_slot.children:
                nonlocal guild

                button.disable()
                try:
                    client = await self.load_account(token.value)

                except LoginFailure:
                    ui.notify("Invalid Token!", type="negative")
                    dialog.classes("animate__animated animate__shakeX")
                    button.enable()
                    await sleep(1)
                    dialog.classes(remove="animate__animated animate__shakeX")
                    return

                with stepper:
                    with ui.step("Now, Choose Your Preferred Guild!") as step:
                        guild = ui.select(
                            options={
                                guild.id: guild.name for guild in client.guilds},
                            with_input=True,
                            on_change=lambda e: ui.notify(e.value),
                        )
                        with ui.stepper_navigation():
                            ui.button("Next", on_click=partial(get_channel, client)).props(
                                "outline"
                            )
                    step.move(target_index=1)
            stepper.next()

        async def get_channel(client: TempClient):
            if stepper.default_slot.children:
                nonlocal channel
                with stepper:
                    with ui.step("Finally, Choose Your Channel!") as step:
                        Guild = client.get_guild(guild.value)
                        channel = ui.select(
                            options={
                                channel.id: channel.name
                                for channel in Guild.channels
                                if isinstance(channel, TextChannel)
                                and channel.permissions_for(Guild.me).send_messages
                            },
                            with_input=True,
                            on_change=lambda e: ui.notify(e.value),
                        )

                        with ui.stepper_navigation():
                            ui.button("Next", on_click=partial(get_features, client)).props(
                                "outline"
                            )
                    step.move(target_index=2)
            stepper.next()

        async def get_features(client: TempClient):
            nonlocal gem, pray, exp, daily, solve, commands, sell, url, ping, ping_self, huntbot
            if stepper.default_slot.children:
                with stepper:
                    with ui.step("Select Features!") as step:
                        with ui.stepper_navigation():
                            with ui.card().classes("w-full q-card-features"):
                                pray = ui.checkbox("Pray Automatically")
                                exp = ui.checkbox(
                                    "Send Messages To Level Up Automatically")
                                daily = ui.checkbox(
                                    "Claim Daily Automatically")

                                with ui.expansion(
                                    "Gems", icon="settings_applications"
                                ).classes("w-full"):
                                    checkbox = ui.checkbox("Enable Using Gems")

                                    gem = ui.checkbox(
                                        "Use Star Gems"
                                    ).bind_visibility_from(checkbox, "value")

                                with ui.expansion(
                                    "Solve Captcha", icon="settings_applications"
                                ).classes("w-full"):
                                    checkbox = ui.checkbox(
                                        "Enable Solving Captcha")

                                    solve = ui.input(
                                        "2captcha APIKEY",
                                        password=True,
                                        password_toggle_button=True,
                                        validation={
                                            "Invalid APIKEY": lambda value: len(value) > 25
                                        },
                                    ).bind_visibility_from(checkbox, "value")

                                with ui.expansion(
                                    "Webhook", icon="settings_applications"
                                ).classes("w-full"):
                                    checkbox = ui.checkbox("Enable Webhook")

                                    url = ui.input(
                                        "Webhook URL",
                                        password=True,
                                        password_toggle_button=True,
                                        validation={
                                            "Invalid Webhook URL": lambda value: value.startswith(
                                                "https://discord.com/api/webhooks"
                                            )
                                        },
                                    ).bind_visibility_from(checkbox, "value")

                                    ping = ui.input(
                                        "USER ID To Ping",
                                        validation={
                                            "Invalid ID": lambda value: value.isnumeric()
                                            and len(value) > 15
                                        },
                                    ).bind_visibility_from(checkbox, "value")

                                    ping_self = ui.checkbox(
                                        "Ping YourSelf Too?"
                                    ).bind_visibility_from(checkbox, "value")

                                with ui.expansion(
                                    "Selfbot Commands", icon="settings_applications"
                                ).classes("w-full"):
                                    checkbox = ui.checkbox(
                                        "Enable Selfbot Commands")

                                    commands = ui.input(
                                        "Enter Selfbot Prefix",
                                        validation={
                                            "Prefix Is Too Long Don't You Think?": lambda value: len(
                                                value
                                            )
                                            < 5
                                        },
                                    ).bind_visibility_from(checkbox, "value")

                                with ui.expansion(
                                    "Sell Animals", icon="settings_applications"
                                ).classes("w-full"):
                                    checkbox = ui.checkbox(
                                        "Enable Selling Animals")

                                    sell = (
                                        ui.select(
                                            [
                                                "Common",
                                                "Uncommon",
                                                "Rare",
                                                "Epic",
                                                "Mythical",
                                                "Gem",
                                                "Legendary",
                                                "Fabled",
                                                "All",
                                            ],
                                            multiple=True,
                                            validation={
                                                'You Should Only Select "All" Alone': lambda value: (
                                                    len(value) < 8 and not "All" in value
                                                )
                                                or (len(value) == 1 and "All" in value),
                                                "Please Pick Animal Type(s) To Sell": lambda value: len(
                                                    value
                                                )
                                                > 0,
                                            },
                                        )
                                        .bind_visibility_from(checkbox, "value")
                                        .props("use-chips")
                                    )

                                with ui.expansion(
                                    "Auto-Huntbot", icon="settings_applications"
                                ).classes("w-full"):
                                    checkbox = ui.checkbox(
                                        "Enable Huntbot Automatically")

                                    huntbot = ui.input(
                                        "Enter The Number of Conwoncies To Hunt",
                                        validation={
                                            "Input Must Be Integer": lambda value: value.isnumeric(),
                                            "You Might Be Spending Too Much?": lambda value: int(value) < 1e10 if value.isnumeric() else True
                                        },
                                    ).bind_visibility_from(checkbox, "value")

                                ui.button(
                                    "Save", on_click=partial(create_data, client)
                                ).props("outline")

                                ui.button(
                                    "Save & Run", on_click=lambda: create_data(client, True)
                                ).props("outline")

                    step.move(target_index=3)
            stepper.next()

        with ui.dialog(value=True) as dialog:
            with ui.stepper().props("vertical").classes("w-full") as stepper:
                with ui.step("First, Enter Your Token!"):
                    token = ui.input(
                        label="Token",
                        password=True,
                        password_toggle_button=True,
                        validation={
                            "Not a valid Token!": lambda value: search(
                                r"[\w-]{24}\.[\w-]{6}\.[\w-]{38}", value
                            )
                        },
                    )
                    with ui.stepper_navigation():
                        ui.button(
                            "Next!", icon="login", on_click=lambda e: get_guild(e.sender)
                        ).props("outline")


class LogElementHandler(logging.Handler):
    """A logging handler that emits messages to a log element."""

    def __init__(self, element: ui.log, level: int = logging.NOTSET) -> None:
        self.element = element
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.element.push(msg)
        except Exception:
            self.handleError(record)


if __name__ in ("__main__", "__mp_main__"):
    gui = GUI()

    gui.main()
    ui.run(title="OwO Selfbot", favicon="favicon.ico")
