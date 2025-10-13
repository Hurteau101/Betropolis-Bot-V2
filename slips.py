from itertools import combinations
from collections import Counter
from redis_manager import RedisManger

class Slips:
    def __init__(self):
        self.redis = RedisManger()

    def valid_group(self, group):
        opponent_count = Counter(player["opponent"] for player in group)
        if not all(count == 1 for count in opponent_count.values()):
            return False

        team_count = Counter(player["team"] for player in group)
        if not all(count == 1 for count in team_count.values()):
            return False

        matches = set()

        for player in group:
            match = frozenset([player["team"], player["opponent"]])

            if match in matches:
                return False
            matches.add(match)

        return True

    def generate_groups(self, differences, slip_size=3):
        used_players = set()
        valid_groups = []

        for group in combinations(differences, slip_size):
            if not self.valid_group(group):
                continue

            group_keys = {
                (player["player_name"], player["stat_type"], player["start_date"])
                for player in group
            }

            if any(player_key in used_players for player_key in group_keys):
                continue

            used_players.update(group_keys)
            valid_groups.append(group)

        self.redis.store_player(differences=valid_groups)
        return valid_groups

    def create_slips(self, differences, slip_size):
        """
        Create slips only from entries that include the primary_book key (e.g., 'parlayplay', 'prizepicks', etc.)
        """
        existing_players = self.redis.check_players(differences)

        new_entries = {
            f"{difference['player_name']}-{difference['stat_type']}-{difference['team']}-{difference['opponent']}-{difference['start_date']}": {
                **difference
            }
            for difference in differences
            if (
                       f"{difference['player_name']}-{difference['stat_type']}-{difference['team']}-{difference['opponent']}-{difference['start_date']}"
                       not in existing_players
               )
               and self.redis.check_past_time(difference["start_date"])
        }

        if not new_entries:
            return None

        return self.generate_groups(differences=new_entries.values(), slip_size=slip_size)