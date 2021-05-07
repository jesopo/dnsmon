import asyncio
from argparse import ArgumentParser

from ircrobots import ConnectionParams, SASLUserPass

from .config import Config, load as config_load
from .timer  import run as run_timer
from .       import Bot

async def main(config: Config):
    bot = Bot(config)

    host, port, tls      = config.server
    sasl_user, sasl_pass = config.sasl

    params = ConnectionParams(
        config.nickname,
        host,
        port,
        tls,
        username=config.username,
        realname=config.realname,
        password=config.password,
        sasl=SASLUserPass(sasl_user, sasl_pass),
        autojoin=[config.channel]
    )
    await bot.add_server(host, params)
    await asyncio.wait([
        run_timer(bot, config),
        bot.run()
    ])

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("config")
    args   = parser.parse_args()

    config = config_load(args.config)
    asyncio.run(main(config))
