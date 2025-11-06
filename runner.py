import random

from parlayPlay import ParlayPlay
from prizePicks import PrizePicks
from underdog import Underdog


class EsportsRunner:
    def run_bot(self):
        # parlay = ParlayPlay()
        # parlay.run_book()
        #
        # underdog = Underdog()
        # underdog.run_book(enable_streak=True)

        parlay = ParlayPlay()
        underdog = Underdog()
        underdog_streak = Underdog()  # separate instance for streaks
        prizepicks = PrizePicks()

        main_bots = [underdog, prizepicks]
        random.shuffle(main_bots)

        bots = [parlay] + main_bots + [underdog_streak]

        for bot in bots:
            print(bot.__str__())

            if bot is underdog_streak:
                bot.run_book(enable_streak=True)
            else:
                bot.run_book()


if __name__ == "__main__":
    runner = EsportsRunner()
    runner.run_bot()
