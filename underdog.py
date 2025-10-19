from esports import Esports
from redis_manager import RedisManger


class Underdog(Esports):
    def __init__(self):
        super().__init__()
        self.additional_information = {
            3: {
                "unit_size": "0.40x",
                "expected_payout": "6x"
            },
            4: {
                "unit_size": "0.25x",
                "expected_payout": "10x"
            }
        }

    def create_streak(self, differences, main_difference=15, secondary_difference=7.5):
        difference_sorted = sorted(differences, key=lambda x: x['difference_percentage'], reverse=True)

        redis = RedisManger(db=6)
        existing_players = redis.check_players(difference_sorted)

        eligible = [
            diff for diff in difference_sorted
            if f"{diff['player_name']}-{diff['stat_type']}-{diff['team']}-{diff['opponent']}-{diff['start_date']}"
               not in existing_players and redis.check_past_time(diff["start_date"])
        ]

        if not eligible:
            return []

        first_player = next((p for p in eligible if p["difference_percentage"] > main_difference), None)

        if first_player is None:
            return []

        second_player = next(
            (p for p in eligible if p != first_player and (p.get("team") != first_player.get("team") or p.get("team") != first_player.get("opponent"))
             and p.get("difference_percentage") > secondary_difference),
            None
        )

        valid_selections = [p for p in [first_player, second_player] if p is not None]

        if len(valid_selections) != 2:
            return []

        if valid_selections:
            redis.store_player(differences=[[player] for player in valid_selections])

        return valid_selections


    def run_book(self, enable_streak=False, main_difference=15, secondary_difference=7.5):
        esports_data = self._get_esports_data()
        if not esports_data:
            return None

        differences = self._create_differences(
            esports_data=esports_data,
            base_book_1="prizepicks",
            base_book_2="underdog",
            compute_average=False,
            difference_threshold=1,
            difference_percentage=10,
            main_book_name="underdog"
        )

        if not enable_streak:
            slips = self._create_slips(difference_lines=differences)
        else:
            slips = self.create_streak(differences=differences, main_difference=main_difference, secondary_difference=secondary_difference)

        self._send_discord_message(slips, "Underdog", self.additional_information, streaks=enable_streak)

if __name__ == "__main__":
    underdog = Underdog()
    underdog.run_book()


