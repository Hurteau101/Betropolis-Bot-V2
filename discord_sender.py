import os
from collections import Counter
from datetime import datetime, timezone
import pytz
from discordwebhook import Discord
from dotenv import load_dotenv


class DiscordBot:
    def __init__(self):
        load_dotenv()
        self.discord_images = {
            "underdog": {
                "image": "https://cdn.discordapp.com/emojis/1327520722209210481.webp?size=96",
                "color": 0xffe733
            },
            "prizepicks": {
                "image": "https://cdn.discordapp.com/emojis/1327520687832829962.webp?size=96",
                "color": 0xa020f0,
            },
            "parlayplay": {
                "image": "https://cdn.discordapp.com/emojis/1350502083043917997.webp?size=96",
                "color": 0xffe733,
            }
        }


    def _slip_fields(self, slip_data, book_name):
        def convert_date(slip_date: str):
            """Convert UTC ISO date string to readable US/Eastern time."""
            try:
                utc = pytz.utc
                eastern = pytz.timezone("US/Eastern")

                slip_date = slip_date.replace("t", "T").rstrip("Z")
                dt = datetime.strptime(slip_date, "%Y-%m-%dT%H:%M:%S")

                dt = utc.localize(dt).astimezone(eastern)

                return dt.strftime("%b %d, %Y @ %I:%M %p %Z")

            except Exception:
                return "N/A"


        main_fields = [
            {
                "name": "",
                "value": (
                    f"⭐ **({slip.get('player_name').upper()})** "
                    f"{slip.get('direction').title()} {slip.get(book_name)} "
                    f"{slip.get('stat_type')} [{slip.get('team')}] ⭐\n"
                    f">>> **Scheduled**: {convert_date(slip.get('start_date', 'N/A'))}"
                ),
                "inline": False,
            }
            for slip in slip_data
        ]
        return main_fields

    def send_message(self, slip, book_name, slip_information):
        discord = Discord(url=os.getenv("DISCORD_WEBHOOK"))
        embed = self._create_message(slip, book_name, slip_information)
        discord.post(embeds=[embed])


    def _create_message(self, slip, book_name, slip_information):
        league_count = Counter(player["league"] for player in slip)
        multi_league = True if len(league_count.keys()) > 1 else False

        if multi_league:
            title = f"Mixed Leagues {slip_information.get('expected_payout', 'N/A')}"
        else:
            title = f"{list(league_count.keys())[0]} {slip_information.get('expected_payout', 'N/A')}"

        fields = []
        fields.append({
            "name": "",
            "value": f"***Unit Size: {slip_information.get('unit_size', 'N/A')}***",

        })

        fields.extend(self._slip_fields(slip, book_name.lower()))

        return {
            "title": title,
            "color": self.discord_images.get(book_name.lower(), {}).get("color", 0xffffff),
            "author": {
                "name": f"{book_name} Slip",
                "icon_url": self.discord_images.get(book_name.lower(), {}).get("image", "")
            },
            "thumbnail": {
                "url": "https://cdn.discordapp.com/emojis/1365557751509684325.webp?size=96"
            },
            "fields": fields,
            "footer": {
                "text": "Powered by Betropolis",
                # "icon_url": "https://cdn.discordapp.com/emojis/1327126577984569384.webp?size=128"
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }





