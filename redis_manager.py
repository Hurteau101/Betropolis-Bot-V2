from datetime import datetime, timezone
import redis

class RedisManger:
    def __init__(self):
        self.redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True, db=5)

    def check_past_time(self, date_time):
        check_time = datetime.fromisoformat(date_time.replace("Z", "")).replace(tzinfo=timezone.utc)
        now_utc = datetime.now(timezone.utc)
        if check_time < now_utc:
            return False
        return True

    def check_players(self, differences):
        redis_client = self.redis_client

        player_keys = [
            f"{difference['player_name']}-{difference['stat_type']}-{difference['team']}-{difference['opponent']}-{difference['start_date']}"
            for difference in differences
        ]

        existing_players = {key for key in player_keys if redis_client.exists(key)}
        return existing_players

    def store_player(self, differences):
        if not differences:
            return

        pipeline = self.redis_client.pipeline()
        for difference in differences:
            for player in difference:
                player_key = f"{player['player_name']}-{player['stat_type']}-{player['team']}-{player['opponent']}-{player['start_date']}"
                match_timestamp = datetime.fromisoformat(player["start_date"]).timestamp()

                pipeline.hset(player_key, mapping=player)
                pipeline.pexpireat(player_key, int(match_timestamp * 1000))

                pipeline.execute()


