from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext import ConversationHandler
from telegram import ReplyKeyboardMarkup
from telegram.ext.filters import Filters

from parser import parse_schedule, parse_buildings


class TelegramBot:
    def __init__(self, api_key):
        self.updater = Updater(api_key, use_context=True)
        self.default_keyboard = [['Узнать занятость аудиторий']]
        self.BUILDING, self.BUILDING_DATE, self.ROOM, self.ROOM_DATES = range(4)

    def run(self):
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.__get_buildings),
                          MessageHandler(Filters.text(self.default_keyboard[0][0]), self.__get_buildings)],
            states={
                self.BUILDING: [MessageHandler(Filters.text & ~Filters.command, self.__get_building_dates)],
                self.BUILDING_DATE: [MessageHandler(Filters.text & ~Filters.command, self.__parse_page)],
                self.ROOM: [MessageHandler(Filters.text & ~Filters.command, self.__choose_date)],
                self.ROOM_DATES: [MessageHandler(Filters.text & ~Filters.command, self.__get_schedule)]
            },
            fallbacks=[CommandHandler("cancel", self.__cancel)],
        )

        self.updater.dispatcher.add_handler(conv_handler)
        self.updater.start_polling()

    def stop(self):
        self.updater.stop()

    def __get_buildings(self, update: Update, context: CallbackContext):
        try:
            buildings = parse_buildings()
        except:
            update.message.reply_text('Упс! Что-то пошло не так...')
            return

        building_name_list = iter(buildings)
        buttons = zip(building_name_list, building_name_list)
        context.user_data['buildings'] = buildings
        update.message.reply_text(
            "Привет! Это бот-парсер расписания занятости аудиторий ВятГУ. Выбери корпус, чтобы узнать занятость аудиторий в нём",
            reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
        )

        return self.BUILDING

    def __get_building_dates(self, update: Update, context: CallbackContext):
        chosen_building = update.message.text.strip()
        context.user_data["chosen_building"] = chosen_building
        if chosen_building not in context.user_data['buildings']:
            update.message.reply_text("Не понимаю тебя")
            return

        building_dates = iter(context.user_data['buildings'][chosen_building])
        buttons = zip(building_dates, building_dates)
        update.message.reply_text(
            'Выберите дату',
            reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
        )

        return self.BUILDING_DATE

    def __parse_page(self, update: Update, context: CallbackContext):
        date = update.message.text.strip()
        building = context.user_data['buildings'][context.user_data['chosen_building']]
        if date not in building:
            update.message.reply_text("Не понимаю тебя")
            return

        try:
            parsed_data = parse_schedule(building[date])
        except:
            update.message.reply_text('Упс! Что-то пошло не так...')
            return

        it = iter(parsed_data)
        buttons = zip(it, it, it)
        context.user_data["schedule"] = parsed_data
        update.message.reply_text(
            'Выберите аудиторию',
            reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
        )

        return self.ROOM

    def __choose_date(self, update: Update, context: CallbackContext):
        chosen_room = update.message.text.strip()
        if chosen_room not in context.user_data["schedule"]:
            update.message.reply_text("Не понимаю тебя")
            return

        it = iter(context.user_data["schedule"][chosen_room])
        buttons = zip(it, it)
        context.user_data["chosen_room"] = chosen_room
        update.message.reply_text(
            'Выберите дату',
            reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
        )

        return self.ROOM_DATES

    def __get_schedule(self, update: Update, context: CallbackContext):
        date = update.message.text.strip()
        room = context.user_data["schedule"][context.user_data["chosen_room"]]
        if date not in room:
            update.message.reply_text("Не понимаю тебя")
            return

        update.message.reply_text(
            self.__convert_dict_to_str(room[date]),
            reply_markup=ReplyKeyboardMarkup(self.default_keyboard, resize_keyboard=True)
        )
        self.__clear_data(context)

        return ConversationHandler.END

    def __convert_dict_to_str(self, dictionary: dict):
        return "\n".join(
            [f"{item[0]}: {'Свободно' if item[1] is None or item[1] == '' or item[1].isspace() else item[1]}" for item
             in dictionary.items()])

    def __cancel(self, update: Update, context: CallbackContext):
        self.__clear_data(context)
        update.message.reply_text(
            'Поговорили',
            reply_markup=ReplyKeyboardMarkup(self.default_keyboard, resize_keyboard=True)
        )
        return ConversationHandler.END

    def __clear_data(self, context):
        if "schedule" in context.user_data:
            del context.user_data["schedule"]
        if "buildings" in context.user_data:
            del context.user_data['buildings']
        if 'chosen_building' in context.user_data:
            del context.user_data['chosen_building']
        if "chosen_room" in context.user_data:
            del context.user_data['chosen_room']
