import asyncio, re
from datetime import datetime
from typing   import List, Optional, Tuple

import aiodns
from irctokens import build
from ircrobots import Bot
from .config   import Config

async def _get_records(
        domain: str,
        type:   str
        ) -> List[str]:

    resolver = aiodns.DNSResolver()
    try:
        oresult = await resolver.query(domain, type)
    except aiodns.error.DNSError:
        return []

    if isinstance(oresult, list):
        results = oresult
    else:
        results = [oresult]

    outs: List[str] = []
    for r in results:
        if   type == "SOA":
            outs.append(
                f"{r.nsname}. {r.hostmaster}. {r.serial}"
                f" {r.refresh} {r.retry} {r.expires}"
            )
        elif type in {"A", "AAAA"}:
            outs.append(r.host)
        elif type == "NS":
            outs.append(f"{r.host}.")
        elif type == "CNAME":
            outs.append(f"{r.cname}.")
        elif type == "MX":
            outs.append(f"{r.priority} {r.host}.")
    return outs

async def run(
        bot:    Bot,
        config: Config):

    while True:
        utcnow  = datetime.utcnow().replace(microsecond=0)
        nextmin = 60-utcnow.second
        await asyncio.sleep(nextmin)

        outs: List[str] = []
        for domain in config.records:
            for dns_type, dns_expected in config.records[domain].items():
                dns_actual = set(await _get_records(domain, dns_type))

                if not dns_actual:
                    if dns_expected:
                        out = f"empty \2{dns_type} {domain}\2"
                        outs.append(out)
                else:
                    dns_unexpected = sorted(dns_actual - dns_expected)
                    if dns_unexpected:
                        out  = f"unexpected \2{dns_type} {domain}\2 ("
                        out += ", ".join(dns_unexpected) + ")"
                        outs.append(out)

        if bot.servers:
            server = list(bot.servers.values())[0]
            for out in outs:
                out = f"WARN: {out}"
                await server.send(build("PRIVMSG", [config.channel, out]))
