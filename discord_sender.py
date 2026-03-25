import platform

from discordwebhook import Discord
from collections import Counter
from datetime import datetime, timezone
import pytz
import io
import os
from PIL import Image, ImageFont
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook
from pilmoji import Pilmoji

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

    def discord_mapper(self, book_name):
        mapper = {
            "underdog": {
                "webhook": os.getenv("DISCORD_WEBHOOK_URL_UNDERDOG"),
                "role_id": os.getenv("DISCORD_UD_ROLE_ID")
            },
            "prizepicks": {
                "webhook": os.getenv("DISCORD_WEBHOOK_URL_PRIZEPICKS"),
                "role_id": os.getenv("DISCORD_PP_ROLE_ID")
            },
            "parlayplay": os.getenv("DISCORD_WEBHOOK_URL_PARLAYPLAY"),
        }

        return mapper.get(book_name.lower())



    @staticmethod
    def _date_formatter(slip_date, date_format="%b %d, %Y @ %I:%M %p %Z"):
        try:
            utc = pytz.utc
            eastern = pytz.timezone("US/Eastern")

            slip_date = slip_date.replace("t", "T").rstrip("Z")
            dt = datetime.strptime(slip_date, "%Y-%m-%dT%H:%M:%S")

            dt = utc.localize(dt).astimezone(eastern)

            return dt.strftime(date_format)
        except:
            return "N/A"

    def _slip_fields(self, slip_data, book_name):
        if book_name.lower() == "prizepicks":
            raw_bet_link = ",".join(link.get("prizepicks_betlink_id") for link in slip_data if link.get("prizepicks_betlink_id"))
            bet_link = f"https://app.prizepicks.com/?projections={raw_bet_link}"


        main_fields = [
            {
                "name": "",
                "value": (
                    f"⭐ **({slip.get('player_name').upper()})** "
                    f"{slip.get('direction').title()} {slip.get(book_name)} "
                    f"{slip.get('stat_type').title()} [{slip.get('team')}] ⭐\n"
                    f">>> **Scheduled**: {DiscordBot._date_formatter(slip.get('start_date', 'N/A'))} \n"
                    f"**Match**: {' vs '.join(sorted([slip.get('team'), slip.get('opponent')]))}"

                ),
                "inline": False,
            }
            for slip in slip_data
        ]

        if book_name.lower() == "prizepicks":
            mapper = {
                'over': 'o',
                'under': 'u'
            }

            raw_bet_link = ",".join(f'{link.get("prizepicks_projection_id")}-{mapper.get(link.get("direction"))}-{link.get("prizepicks")}'
                                    for link in slip_data if link.get("prizepicks_projection_id"))
            bet_link = f"https://app.prizepicks.com/?projections={raw_bet_link}"

            main_fields.append({
                "name": "📲 PrizePick Link",
                "value": f"[Bet on PrizePicks]({bet_link})",
                "inline": False
            })


        return main_fields

    def send_message(self, slip, book_name, slip_information, streaks=False):
        if not streaks:
            book_mapping = self.discord_mapper(book_name)
            webhook_url = book_mapping.get("webhook")
            role_id = book_mapping.get("role_id")
            discord = Discord(url=webhook_url)
            embed = self._create_message(slip, book_name, slip_information)
            discord.post(
                content=f"<@&{role_id}>" if role_id else "",
                embeds=[embed]
            )
        else:
            self.streaks_image(players=slip, role_id=os.getenv("DISCORD_UD_ROLE_ID"))

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

    def get_font(size: int = 38):
        system = platform.system()

        if system == "Windows":
            font_path = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "seguisym.ttf")
        elif system == "Linux":
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        else:
            font_path = "/Library/Fonts/Arial Unicode.ttf"

        try:
            font = ImageFont.truetype(font_path, size)
        except Exception as e:
            print(f"⚠️ Font load failed ({font_path}): {e}")
            font = ImageFont.load_default()

        return font

    def streaks_image(self, players: list[dict], role_id: str | int):
        def draw_bold_text(draw, position, text, font, fill, offset=1):
            x, y = position
            for dx, dy in [(0, 0), (offset, 0), (0, offset), (offset, offset)]:
                draw.text((x + dx, y + dy), text, font=font, fill=fill)

        # Base image
        streak_starter_image = Image.open("starter_image.png").convert("RGBA")

        # Fonts
        try:
            # font_main = ImageFont.truetype("seguisym.ttf", 38)  # supports ★
            # font_time = ImageFont.truetype("seguisym.ttf", 38)
            font_main = DiscordBot.get_font(38)
            font_time = DiscordBot.get_font(38)
        except:
            font_main = ImageFont.load_default()
            font_time = ImageFont.load_default()

        # Colors
        white = (255, 255, 255, 255)
        shadow = (0, 0, 0, 255)
        yellow = (255, 215, 0, 255)

        # Positioning
        x = streak_starter_image.width * 0.08
        y = streak_starter_image.height * 0.45
        line_spacing = 130

        with Pilmoji(streak_starter_image) as pilmoji:
            for i, player in enumerate(players):
                base_y = y + (i * line_spacing)
                time_y = base_y + 55

                # Text
                main_text = (
                    f"★ ({player.get('player_name').upper()}) {player.get('underdog')} {player.get('direction')} "
                    f"{player.get('stat_type').title()} {player.get('team')} ★")
                time_text = DiscordBot._date_formatter(player.get("start_date"), "%Y-%m-%d %H:%M ET")

                # Shadow for main text
                pilmoji.text((int(x + 2), int(base_y + 2)), main_text, font=font_main, fill=shadow)

                # Foreground text (bolded)
                for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                    pilmoji.text((int(x + dx), int(base_y + dy)), main_text, font=font_main, fill=white)

                # Color only the stars
                star_width = font_main.getlength("★")
                pilmoji.text((int(x), int(base_y)), "★", font=font_main, fill=yellow)

                # Find where the last star should go
                text_width = font_main.getlength(main_text)
                pilmoji.text((int(x + text_width - star_width), int(base_y)), "★", font=font_main, fill=yellow)

                # Time text below (also left-aligned)
                pilmoji.text((int(x + 2), int(time_y + 2)), time_text, font=font_time, fill=shadow)
                pilmoji.text((int(x), int(time_y)), time_text, font=font_time, fill=white)

        # Save to memory
        buffer = io.BytesIO()
        streak_starter_image.save(buffer, format="PNG")
        buffer.seek(0)

        # Send to Discord
        webhook = DiscordWebhook(
            content=f"<@&{role_id}>" if role_id else "",
            url=os.getenv("DISCORD_WEBHOOK_URL_UNDERDOG_STREAKS")
        )
        webhook.add_file(file=buffer.getvalue(), filename="streaks.png")
        webhook.execute()

#
# class DiscordBot:
#     def __init__(self):
#         load_dotenv()
#         self.discord_images = {
#             "underdog": {
#                 "image": "https://cdn.discordapp.com/emojis/1327520722209210481.webp?size=96",
#                 "color": 0xffe733
#             },
#             "prizepicks": {
#                 "image": "https://cdn.discordapp.com/emojis/1327520687832829962.webp?size=96",
#                 "color": 0xa020f0,
#             },
#             "parlayplay": {
#                 "image": "https://cdn.discordapp.com/emojis/1350502083043917997.webp?size=96",
#                 "color": 0xffe733,
#             }
#         }
#
#
#     def send_message(self, slip, book_name, slip_information):
#         # discord = Discord(url=os.getenv("DISCORD_WEBHOOK"))
#         # embed = self._create_message(slip, book_name, slip_information)
#         # discord.post(embeds=[embed])
#         players = [
#             {
#                 "player_name": "s1mple",
#                 "line": 10.5,
#                 "direction": "Over",
#                 "stat_type": "Kills",
#                 "team": "NAVI",
#                 "scheduled": "2025-05-10 15:00 ET"
#             },
#             {
#                 "player_name": "ZywOo",
#                 "line": 7.5,
#                 "direction": "Under",
#                 "stat_type": "Headshots",
#                 "team": "Vitality",
#                 "scheduled": "2025-05-10 15:00 ET"
#             }
#         ]
#         self.streaks_image(players)
#
#     def streaks_image(self, players: list[dict]):
#         """
#         Draws up to 2 player lines on starter_image and sends it to Discord.
#
#         Expected player format:
#         {
#             "player_name": "s1mple",
#             "direction": "Over",
#             "stat_type": "Kills",
#             "team": "NAVI",
#             "line": "23.5",
#             "scheduled": "2025-05-10 15:00 ET"
#         }
#         """
#         import io
#         import os
#         from PIL import Image, ImageFont
#         from dotenv import load_dotenv
#         from discord_webhook import DiscordWebhook
#         from pilmoji import Pilmoji
#
#         load_dotenv()
#
#         # Base image
#         img = Image.open("starter_image.png").convert("RGBA")
#
#         # Fonts
#         try:
#             font_main = ImageFont.truetype("seguisym.ttf", 38)  # supports ★
#             font_time = ImageFont.truetype("seguisym.ttf", 38)
#         except:
#             font_main = ImageFont.load_default()
#             font_time = ImageFont.load_default()
#
#         # Colors
#         white = (255, 255, 255, 255)
#         shadow = (0, 0, 0, 255)
#         yellow = (255, 215, 0, 255)
#
#         # Vertical positioning
#         y = img.height * 0.45
#         line_spacing = 130
#
#         with Pilmoji(img) as pilmoji:
#             for i, player in enumerate(players[:2]):
#                 base_y = y + (i * line_spacing)
#                 time_y = base_y + 55
#
#                 # Build text with one star at each end
#                 main_text = f"★ ({player['player_name'].upper()}) {player['line']} {player['direction']} {player['stat_type']} {player['team']} ★"
#                 time_text = player["scheduled"]
#
#                 # Center horizontally
#                 text_width = font_main.getlength(main_text)
#                 x_centered = (img.width - text_width) / 2
#
#                 # --- Shadow layer ---
#                 pilmoji.text((int(x_centered + 2), int(base_y + 2)), main_text, font=font_main, fill=shadow)
#
#                 # --- Foreground layer (all white first) ---
#                 pilmoji.text((int(x_centered), int(base_y)), main_text, font=font_main, fill=white)
#
#                 # --- Recolor the first and last stars yellow ---
#                 # Measure first star width and last star position
#                 star_width = font_main.getlength("★")
#                 pilmoji.text((int(x_centered), int(base_y)), "★", font=font_main, fill=yellow)
#                 pilmoji.text((int(x_centered + text_width - star_width), int(base_y)), "★", font=font_main, fill=yellow)
#
#                 # --- Time line below (centered) ---
#                 time_width = font_time.getlength(time_text)
#                 time_x = (img.width - time_width) / 2
#                 pilmoji.text((int(time_x + 2), int(time_y + 2)), time_text, font=font_time, fill=shadow)
#                 pilmoji.text((int(time_x), int(time_y)), time_text, font=font_time, fill=white)
#
#         # Save to memory
#         buffer = io.BytesIO()
#         img.save(buffer, format="PNG")
#         buffer.seek(0)
#
#         # Send to Discord
#         webhook = DiscordWebhook(url=os.getenv("DISCORD_WEBHOOK"))
#         webhook.add_file(file=buffer.getvalue(), filename="streaks.png")
#         webhook.execute()

    # def send_streaks_image(self, players: list[dict], book_name: str = "Underdog"):
    #     """
    #     Draws up to 2 player lines on starter_image and sends it to Discord with color and author embed info.
    #
    #     Expected player format:
    #     {
    #         "player_name": "s1mple",
    #         "direction": "Over",
    #         "stat_type": "Kills",
    #         "team": "NAVI",
    #         "line": "23.5",
    #         "scheduled": "2025-05-10 15:00 ET"
    #     }
    #     """
    #     import io
    #     import os
    #     from PIL import Image, ImageFont
    #     from dotenv import load_dotenv
    #     from discord_webhook import DiscordWebhook, DiscordEmbed
    #     from pilmoji import Pilmoji
    #
    #     load_dotenv()
    #
    #     # Base image
    #     img = Image.open("starter_image.png").convert("RGBA")
    #
    #     # Fonts
    #     try:
    #         font_main = ImageFont.truetype("seguisym.ttf", 48)  # ✅ supports ★ characters
    #         font_time = ImageFont.truetype("seguisym.ttf", 48)
    #     except:
    #         font_main = ImageFont.load_default()
    #         font_time = ImageFont.load_default()
    #
    #     # Colors
    #     white = (255, 255, 255, 255)
    #     shadow = (0, 0, 0, 255)
    #     yellow = (255, 215, 0, 255)
    #
    #     # Positioning
    #     x = img.width * 0.08
    #     y = img.height * 0.45
    #     line_spacing = 130
    #
    #     with Pilmoji(img) as pilmoji:
    #         for i, player in enumerate(players[:2]):
    #             base_y = y + (i * line_spacing)
    #             time_y = base_y + 55
    #
    #             # Construct text (text-based stars)
    #             left_star = "★"
    #             right_star = "★"
    #             main_text = f"({player['player_name'].upper()}) {player['line']} {player['direction']} {player['stat_type']} {player['team']}"
    #             time_text = player["scheduled"]
    #
    #             # Shadow
    #             pilmoji.text((int(x + 2), int(base_y + 2)), left_star, font=font_main, fill=shadow)
    #             pilmoji.text((int(x + 2 + 35), int(base_y + 2)), main_text, font=font_main, fill=shadow)
    #
    #             # Bold + glow effect
    #             for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
    #                 pilmoji.text((int(x + dx), int(base_y + dy)), left_star, font=font_main, fill=yellow)
    #                 pilmoji.text((int(x + 35 + dx), int(base_y + dy)), main_text, font=font_main, fill=white)
    #
    #             # Right star
    #             text_width = font_main.getlength(main_text)
    #             pilmoji.text((int(x + 35 + text_width + 10), int(base_y)), right_star, font=font_main, fill=yellow)
    #
    #             # Time below
    #             pilmoji.text((int(x + 2), int(time_y + 2)), time_text, font=font_time, fill=shadow)
    #             pilmoji.text((int(x), int(time_y)), time_text, font=font_time, fill=white)
    #
    #     # Save image to buffer
    #     buffer = io.BytesIO()
    #     img.save(buffer, format="PNG")
    #     buffer.seek(0)
    #
    #     # Discord configuration
    #     webhook_url = os.getenv("DISCORD_WEBHOOK")
    #     webhook = DiscordWebhook(url=webhook_url)
    #
    #     # --- NEW: Add embed with color + author logo ---
    #     embed_color = self.discord_images.get(book_name.lower(), {}).get("color", 0xffffff)
    #     embed_author_name = "\u200b"
    #     embed_author_icon = self.discord_images.get(book_name.lower(), {}).get("image", "")
    #
    #     embed = DiscordEmbed(
    #         color=embed_color
    #     )
    #
    #     embed.set_author(name=embed_author_name, icon_url=embed_author_icon)
    #     embed.set_image(url="attachment://streaks.png")
    #
    #     webhook.add_embed(embed)
    #     webhook.add_file(file=buffer.getvalue(), filename="streaks.png")
    #
    #     webhook.execute()





