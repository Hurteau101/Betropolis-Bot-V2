from esports import Esports


class PrizePicks(Esports):
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

    def run_book(self):
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
            main_book_name="prizepicks"
        )

        slips = self._create_slips(
            difference_lines=differences,
        )

        self._send_discord_message(slips, "Prizepicks", self.additional_information)

        # with open("esports_differences_prize_slips.json", "w") as file:
        #     import json
        #     json.dump(slips, file, indent=4)

        # with open("esports_differences_prize.json", "w") as file:
        #     import json
        #     json.dump(differences, file, indent=4)


if __name__ == "__main__":
    underdog = PrizePicks()
    underdog.run_book()


