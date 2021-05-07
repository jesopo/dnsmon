import asyncio, re
from datetime import datetime
from typing   import List, Optional, Tuple

import dns.asyncresolver, dns.resolver
from irctokens import build
from ircrobots import Bot
from .config   import Config

async def _get_records(
        domain:      str,
        type:        str,
        nameservers: List[str]
        ) -> List[str]:

    resolver = dns.asyncresolver.Resolver(configure=False)
    resolver.nameservers = nameservers
    try:
        result = await resolver.resolve(domain, type)
    except dns.resolver.NoAnswer:
        return []

    outs: List[str] = []
    for r in result.rrset:
        outs.append(r.to_text())
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
                dns_actual = set(await _get_records(
                    domain, dns_type, config.nameservers
                ))

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
