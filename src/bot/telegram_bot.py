from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext import ConversationHandler
from telegram import ReplyKeyboardMarkup
from telegram.ext.filters import Filters
from src.parser import parse_schedule


class TelegramBot:
    def __init__(self, api_key):
        self.updater = Updater(api_key, use_context=True)
        self.LINK, self.ROOMS, self.DATES = range(3)

    def run(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("parse", self.__start)],
            states={
                self.LINK: [MessageHandler(Filters.text, self.__parse_page)],
                self.ROOMS: [MessageHandler(Filters.text, self.__choose_date)],
                self.DATES: [MessageHandler(Filters.text, self.__get_schedule)]
            },
            fallbacks=[CommandHandler("cancel", self.__cancel)],
        )

        self.updater.dispatcher.add_handler(conv_handler)
        self.updater.start_polling()

    def stop(self):
        self.updater.stop()

    def __start(self, update: Update, context: CallbackContext):
        update.message.reply_text("Отправьте ссылку на расписание занятости аудиторий")
        return self.LINK

    def __parse_page(self, update: Update, context: CallbackContext):
        parsed_data = parse_schedule(update.message.text.strip())
        it = iter(parsed_data)
        buttons = zip(it, it, it)
        context.user_data["schedule"] = parsed_data
        update.message.reply_text(
            'Выберите аудиторию',
            reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
        )

        return self.ROOMS

    def __choose_date(self, update: Update, context: CallbackContext):
        chosen_room = update.message.text.strip()
        it = iter(context.user_data["schedule"][chosen_room])
        buttons = zip(it, it)
        context.user_data["chosen_room"] = chosen_room
        update.message.reply_text(
            'Выберите дату',
            reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
        )

        return self.DATES

    def __get_schedule(self, update: Update, context: CallbackContext):
        response = context.user_data["schedule"][context.user_data["chosen_room"]][update.message.text.strip()]
        update.message.reply_text(self.__convert_dict_to_str(response))
        del context.user_data["schedule"]

        return ConversationHandler.END

    def __convert_dict_to_str(self, dictionary: dict):
        return "\n".join([f"{item[0]}: {'Свободно' if item[1] is None or item[1] == '' or item[1].isspace() else item[1]}" for item in dictionary.items()])

    def __cancel(self, update: Update, context: CallbackContext):
        del context.user_data["schedule"]
        update.message.reply_text('Поговорили')
        return ConversationHandler.END
