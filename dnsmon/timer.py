import asyncio, re
from datetime import datetime
from typing   import List, Optional, Tuple

import dns.asyncquery, dns.message, dns.resolver
from irctokens import build
from ircrobots import Bot
from .config   import Config

async def _get_records(
        domain:     str,
        rtype:      str,
        nameserver: str
        ) -> List[str]:

    query  = dns.message.make_query(domain, rtype)
    result = await dns.asyncquery.udp(query, nameserver)

    outs: List[str] = []
    for rrset in result.answer:
        for r in rrset:
            outs.append(r.to_text())
    return outs

async def run(
        bot:    Bot,
        config: Config):

    last_values: Dict[str, Dict[str, Set[str]]] = {}

    while True:
        utcnow  = datetime.utcnow().replace(microsecond=0)
        nextmin = 60-utcnow.second
        await asyncio.sleep(nextmin)

        outs: List[Tuple[bool, str]] = []
        for domain in config.records:
            for dns_type, dns_expected in config.records[domain].items():
                dns_actual = set(await _get_records(
                    domain, dns_type, config.nameserver
                ))

                type_format = f"\2{dns_type} {domain}\2"
                if not dns_actual:
                    if dns_expected:
                        outs.append((True, f"empty {type_format}"))
                else:
                    dns_unexpected = sorted(dns_actual - dns_expected)
                    if dns_unexpected:
                        unexpected_s = ", ".join(dns_unexpected)
                        out = f"unexpected {type_format} ({unexpected_s})"
                        outs.append((True, out))

                if not domain in last_values:
                    last_values[domain] = {}

                if (not dns_type in last_values[domain] or
                        not dns_actual == last_values[domain][dns_type]):

                    outs.append((False, f"changed {type_format}"))

                    if dns_type in last_values[domain]:
                        last_actual = last_values[domain][dns_type]
                        was_s = ", ".join(sorted(last_actual))
                        outs.append((False, f"  was: {was_s}"))

                    now_s = ", ".join(sorted(dns_actual))
                    outs.append((False, f"  now: {now_s}"))

                last_values[domain][dns_type] = dns_actual

        if bot.servers:
            server = list(bot.servers.values())[0]
            for warn, out in outs:
                if warn:
                    out = f"WARN: {out}"
                    if not config.channel_warn == config.channel_info:
                        await server.send(
                            build("PRIVMSG", [config.channel_warn, out])
                        )
                else:
                    out = f"INFO: {out}"

                await server.send(
                    build("PRIVMSG", [config.channel_info, out])
                )
