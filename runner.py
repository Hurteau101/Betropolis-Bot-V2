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

        # parlay = ParlayPlay()
        underdog = Underdog()
        underdog_streak = Underdog()  # separate instance for streaks
        prizepicks = PrizePicks()

        main_bots = [underdog, prizepicks]
        random.shuffle(main_bots)

        bot_data = {
            "underdog_1": {
                "class": underdog,
                "slip_size": 3,
                "difference_threshold": 1,
                "difference_percentage": 10,
            },
            "underdog_2": {
                "class": underdog,
                "slip_size": 2,
                "difference_threshold": 1,
                "difference_percentage": 15,
            },
            "streaks": {
                "class": underdog_streak,
                "slip_size": 1,
                "run_streak": True,
                "difference_threshold": 1,
                "difference_percentage": 20,
            },
            "prizepicks": {
                "class": prizepicks,
                "slip_size": 3,
                "difference_threshold": 1,
                "difference_percentage": 10,
            }
        }

        bots = list(bot_data.items())
        bots = dict(bots)

        # bots = main_bots + [underdog_streak]
        #
        for bot in bots.values():
            print(bot.get("class").__str__())

            is_streak = bot.get("run_streak", False)
            slip_size = bot.get("slip_size", 3)
            bot_class = bot.get("class")
            difference_threshold = bot.get("difference_threshold", 10)
            difference_percentage = bot.get("difference_percentage", 15)

            if is_streak:
                bot_class.run_book(enable_streak=True, slip_size=slip_size, difference_threshold=difference_threshold, difference_percentage=difference_percentage)
            else:
                bot_class.run_book(slip_size=slip_size, difference_threshold=difference_threshold, difference_percentage=difference_percentage)


if __name__ == "__main__":
    runner = EsportsRunner()
    runner.run_bot()
