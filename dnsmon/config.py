from dataclasses import dataclass
from os.path     import expanduser
from re          import compile as re_compile
from typing      import Dict, List, Pattern, Set, Tuple

import yaml

@dataclass
class Config(object):
    server:       Tuple[str, int, bool]
    nickname:     str
    username:     str
    realname:     str
    password:     str
    channel_info: str
    channel_warn: str
    sasl:         Tuple[str, str]
    nameserver:   str
    records:      Dict[str, Dict[str, Set[str]]]


def load(filepath: str):
    with open(filepath) as file:
        config_yaml = yaml.safe_load(file.read())

    nickname = config_yaml["nickname"]

    server   = config_yaml["server"]
    hostname, port_s = server.split(":", 1)
    tls      = False

    if port_s.startswith("+"):
        tls    = True
        port_s = port_s.lstrip("+")
    port = int(port_s)

    records: Dict[str, Dict[str, Set[str]]] = {}
    for domain, types in config_yaml["records"].items():
        records[domain] = {}
        for type, results in types.items():
            records[domain][type.upper()] = set(results)

    return Config(
        (hostname, port, tls),
        nickname,
        config_yaml.get("username", nickname),
        config_yaml.get("realname", nickname),
        config_yaml["password"],
        config_yaml["channel-info"],
        config_yaml["channel-warn"],
        (config_yaml["sasl"]["username"], config_yaml["sasl"]["password"]),
        config_yaml["nameserver"],
        records
    )
