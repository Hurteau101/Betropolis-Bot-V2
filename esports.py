import os
from collections import defaultdict, Counter
import requests
from dotenv import load_dotenv
from itertools import combinations

from discord_sender import DiscordBot
from slips import Slips
from abc import ABC, abstractmethod

class Esports(ABC):
    FILTERS = {
        "underdog": 1,
        "prizepicks": 1,
        "parlayplay": 1.77
    }

    def __init__(self):
        load_dotenv()

    def _get_esports_data(self):
        """Fetch esports data from the API."""
        url = "https://api.differentodds.com/dfs/esport_lines/differences"

        params = {
            "books": [
                "underdog",
                "prizepicks",
                "parlayplay"
            ]
        }

        headers = {
            'X-API-KEY': os.getenv("X-API-KEY"),
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()

            # Ensure it is a dictionary before accessing values
            if isinstance(data, dict):
                return list(response.json().values())

            return []

        else:
            print("Error fetching data:", response.status_code, response.text)


        return None

    def _2_book_comparison(self, player, additional_information, main_book_name, book_1, book_2,
                           difference_threshold, difference_percentage):

        difference_amount = abs(book_1["line"] - book_2["line"])
        difference_percent = self._create_difference_percentage(book_1["line"], book_2["line"], difference_amount)

        if difference_amount < difference_threshold or difference_percent < difference_percentage:
            return None

        main_book = book_1 if book_1["book_name"] == main_book_name else book_2
        secondary_book = book_2 if book_1["book_name"] == main_book_name else book_1

        if main_book["line"] < secondary_book["line"]:
            direction = "over"
        else:
            direction = "under"

        return {
            "player_name": player["player_name"],
            **additional_information,
            "stat_type": player["stat_type"],
            book_1["book_name"]: book_1["line"],
            book_2["book_name"]: book_2["line"],
            "difference": difference_amount,
            "difference_percentage": difference_percent,
            "direction": direction,
        }

    def _multiple_book_comparison(self, player, additional_information, book_1, book_2, compare_book,
                                  difference_threshold, difference_percentage):

        average_line = self._create_average(primary_books=[book_1, book_2])

        if not average_line:
            return None

        difference_amount = abs(compare_book["line"] - average_line)
        difference_percent = self._create_difference_percentage(average_line, compare_book["line"], difference_amount)

        if difference_amount < difference_threshold or difference_percent < difference_percentage:
            return None

        if compare_book["line"] < average_line:
            direction = "over"
        else:
            direction = "under"

        return {
            "player_name": player["player_name"],
            **additional_information,
            "stat_type": player["stat_type"],
            book_1["book_name"]: book_1["line"],
            book_2["book_name"]: book_2["line"],
            compare_book["book_name"]: compare_book["line"],
            "average_line": average_line,
            "difference": difference_amount,
            "difference_percentage": difference_percent,
            "direction": direction,
        }

    def _has_both_directions(self, book):
        directions = book.get("directions", [])
        return len(directions) == 2 and all(d.get("multiplier") == 1 for d in directions)

    def _create_differences(self, esports_data, base_book_1, base_book_2, main_book_name=None, compare_book=None, compute_average=False,
                            difference_threshold: float=1, difference_percentage:int=10):
        if compute_average and not compare_book:
            raise ValueError("other_book must be provided when compute_average is True")

        if not main_book_name and not compute_average:
            raise ValueError("main_book_name must be provided when compute_average is False")

        results = []

        for player in esports_data:
            books = self._filter_books(player.get("books", []))
            num_books = len(books)

            if num_books < 2:
                continue

            book_lines = {
                book["book_name"]: book
                for book in books
                if self._has_both_directions(book)
            }

            book_1 = book_lines.get(base_book_1)
            book_2 = book_lines.get(base_book_2)

            if not book_1 or not book_2:
                continue

            projection_id_book_1 = book_1.get("betlink", {}).get("raw_projection_id")
            projection_id_book_2 = book_2.get("betlink", {}).get("raw_projection_id")

            additional_information = {
                "league": player.get("league"),
                "team": player.get("player_team"),
                "opponent": player.get("opponent"),
                "start_date": player.get("start_date"),
                f"{book_1.get('book_name')}_projection_id": projection_id_book_1 if projection_id_book_1 else "",
                f"{book_2.get('book_name')}_projection_id": projection_id_book_2 if projection_id_book_2 else "",
            }

            if not compute_average:
                difference = self._2_book_comparison(
                    player=player,
                    additional_information=additional_information,
                    book_1=book_1,
                    book_2=book_2,
                    difference_threshold=difference_threshold,
                    difference_percentage=difference_percentage,
                    main_book_name=main_book_name,
                )

                if difference:
                    results.append(difference)
            else:
                other_book = book_lines.get(compare_book)

                if not other_book:
                    continue

                difference = self._multiple_book_comparison(
                    player=player,
                    additional_information=additional_information,
                    book_1=book_1,
                    book_2=book_2,
                    compare_book=other_book,
                    difference_threshold=difference_threshold,
                    difference_percentage=difference_percentage,
                )

                if difference:
                    results.append(difference)

        return results

    @abstractmethod
    def run_book(self):
        raise NotImplementedError("Subclasses must implement run_book method")

    def _create_slips(self, difference_lines, slip_size=3):
        slips = Slips()
        return slips.create_slips(
            differences=difference_lines,
            slip_size=slip_size,
        )

    def _filter_books(self, books):
        """Filter out books with any non-standard multiplier"""
        valid_books = []
        for book in books:
            name = book["book_name"]

            # Get expected multiplier for the book
            expected_multiplier = self.FILTERS.get(name)

            if expected_multiplier is None:
                continue

            directions = book.get("directions", [])
            if not directions:
                continue

            # Ensure both directions match the expected multiplier
            if all(d["multiplier"] == expected_multiplier for d in directions):
                valid_books.append(book)

        return valid_books

    def _create_average(self, primary_books):
        """Compute the average line between the two primary books."""
        lines = [
            avg.get("line")
            for avg in primary_books
            if "line" in avg and isinstance(avg.get("line"), (float, int))
        ]

        if len(lines) < 2:
            return None

        return round(sum(lines) / len(lines), 2)

    def _create_difference_percentage(self, line1, line2, difference_amount):
        return round(difference_amount / abs((line1 + line2) / 2) * 100, 2)

    def _send_discord_message(self, slips, book_name, slip_information, streaks=False):
        if slips:
            discord = DiscordBot()

            # Conditional handling for streaks
            if streaks:
                discord.send_message(slip=slips, book_name="Underdog", slip_information=None, streaks=streaks)
            else:
                for slip in slips:
                    slip_length = len(slip)
                    slip_info = slip_information[slip_length]

                    if not slip_info:
                        continue

                    discord.send_message(slip=slip, book_name=book_name, slip_information=slip_info, streaks=streaks)







if __name__ == "__main__":
    esports = Esports()
    esports.runner()
