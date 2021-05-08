from irctokens import build, Line
from ircrobots import Bot as BaseBot
from ircrobots import Server as BaseServer
from ircrobots import ConnectionParams
from ircstates.numerics import *

from .config  import Config

class Server(BaseServer):
    def __init__(self,
            bot:    BaseBot,
            name:   str,
            config: Config):

        super().__init__(bot, name)
        self._config  = config

    async def line_read(self, line: Line):
        if line.command == RPL_WELCOME:
            await self.send(build("MODE", [self.nickname, "+g"]))

    def line_preread(self, line: Line):
        print(f"< {line.format()}")
    def line_presend(self, line: Line):
        print(f"> {line.format()}")

class Bot(BaseBot):
    def __init__(self, config: Config):
        super().__init__()
        self._config = config

    def create_server(self, name: str):
        return Server(self, name, self._config)

