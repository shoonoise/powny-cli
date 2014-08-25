from colorama import Fore, Style
from itertools import cycle


class Colorfull:
    nodes = {}
    colors = cycle((Fore.BLUE, Fore.MAGENTA, Fore.CYAN))

    @classmethod
    def get_node(cls, node, _):
        if node in cls.nodes:
            return cls.nodes[node]
        else:
            cls.nodes[node] = '{}{}{}'.format(next(cls.colors), node, Style.RESET_ALL)
            return cls.nodes[node]

    @classmethod
    def get_level(cls, level, _):
        return {'DEBUG': '{}{}{}'.format(Fore.WHITE, level, Style.RESET_ALL),
                'INFO': '{}{}{}'.format(Fore.GREEN, level, Style.RESET_ALL)}.get(level.strip(), level)

    @classmethod
    def timestamp(cls, timestamp, _):
        return '{}{}{}'.format(Fore.YELLOW, timestamp, Style.RESET_ALL)
