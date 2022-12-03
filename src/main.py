from bot import TelegramBot

from dotenv import load_dotenv
from os import getenv


def main():
    load_dotenv()
    bot = TelegramBot(getenv('TELEGRAM_BOT_API_TOKEN'))
    bot.run()


if __name__ == '__main__':
    main()
