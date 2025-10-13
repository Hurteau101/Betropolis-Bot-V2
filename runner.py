import random

from parlayPlay import ParlayPlay
from prizePicks import PrizePicks
from underdog import Underdog


class EsportsRunner:
    def run_bot(self):
        parlay, underdog, prizepicks = ParlayPlay(), Underdog(), PrizePicks()
        bots = [parlay, underdog, prizepicks]
        random.shuffle(bots)

        for bot in bots:
            print(bot.__str__())
            bot.run_book()


if __name__ == "__main__":
    runner = EsportsRunner()
    runner.run_bot()
