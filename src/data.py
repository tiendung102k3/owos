from json import load, dump
from typing import Any, Self, Literal
from dataclasses import dataclass, field, asdict


@dataclass
class Data:
    data: dict[str, Any] = None  # Data from config.json file

    name: str = None  # Name of The Account
    token: str = None  # Authorization Token
    channel: int = None  # Channel ID
    guild: int = None  # Guild ID
    pray: bool = False  # Pray Mode
    exp: bool = False  # Send Messages to Level Up Or Not
    commands: str = None  # Selfbot Commands Prefix
    daily: bool = False  # Claim Daily
    _sell: list[Literal["Common", "Uncommon", "Rare", "Epic",
                        "Mythical", "Gem", "Legendary", "Fabled"]] | Literal["All"] = None
    # Sell Animals Mode
    solve: str = None  # Captcha Solving (APIKEY)
    _huntbot: int = None
    gem: dict[str, bool] = field(
        default_factory=lambda: dict(enabled=False, star=False))  # Gem Mode
    webhook: dict[str, str | int] = field(
        default_factory=lambda: dict(url=None, ping=None, ping_self=None))
    # Webhook Configuration

    @property
    def sell(self) -> list[Literal["Common", "Uncommon", "Rare", "Epic", "Mythical", "Gem", "Legendary", "Fabled"]] | Literal["All"]:
        return self._sell

    @sell.setter
    def sell(self, value: list[str]) -> None:
        if "All" in value:
            self._sell = "All"
        else:
            self._sell = value

    @property
    def huntbot(self) -> int:
        return self._huntbot

    @huntbot.setter
    def huntbot(self, value) -> None:
        if str(value).isnumeric():
            self._huntbot = int(value)
        else:
            self._huntbot = False

    def __post_init__(self):
        with open("config.json", "r") as f:
            self.data = load(f)

    @staticmethod
    def get_account() -> list[str]:
        """
        Get all account names

        :return: list - all account names
        """

        with open("config.json", "r") as f:
            return [account for account in load(f)]

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if k != "data"}

    def load(self, account: str) -> Self:
        for key, value in self.data[account].items():
            setattr(self, key, value)

        self.name = account

        return self

    def save(self, account: str, data: dict) -> Self:
        """
        Save account data to file.

        :param account: str - the account to save data for
        :param data: dict - the data to save
        :return : Self - the account's data
        """
        self.data.update({account: data})

        with open("config.json", 'w') as f:
            dump(self.data, f, ensure_ascii=False, indent=4)

        return self

    def remove(self, account: str) -> None:
        """
        Remove account data from file.

        :param account: str - the account to remove data for
        :return: None
        """
        self.data.pop(account, None)

        with open("config.json", 'w') as f:
            dump(self.data, f, ensure_ascii=False, indent=4)
