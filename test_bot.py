import telebot as tb
from telebot import types
import parser
import sql
from memory_profiler import memory_usage


class WeatherBot(tb.TeleBot):
    # creating virtual keyboards for bot's users
    start_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = types.KeyboardButton("Узнать погоду")
    start_markup.add(start_button)

    forecasts_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    remember_city_button = types.KeyboardButton("Запомнить населенный пункт")
    today = types.KeyboardButton("Прогноз на сегодня")
    fc_for_5days = types.KeyboardButton('Прогноз на 5 дней')
    fc_for_10days = types.KeyboardButton('Прогноз на 10 дней')
    forecasts_markup.add(remember_city_button, today, fc_for_5days, fc_for_10days)

    def start(self, message):
        remembered_cities = sql.select_user_cities(message.from_user.id)
        sql.update_user_current_markup(message.from_user.id, 'cities_markup')
        if remembered_cities:
            user_city_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            city_buttons = [types.KeyboardButton(name) for name in remembered_cities]
            user_city_markup.add(*city_buttons)
            self.send_message(message.chat.id, 'Введите название города', reply_markup=user_city_markup)
        else:
            self.send_message(message.chat.id, 'Введите название города', reply_markup=types.ReplyKeyboardRemove())

    # this func takes the name of the city and calls two times
    def check_city(self, message):
        text = message.text[0].upper() + message.text[1:]
        cities_result = sql.select_city_name(text)
        # the first call, when forms reply keyboard markup. it works like browser searcher in the dict of cities
        if len(cities_result) > 1 or (len(cities_result) == 1 and text != cities_result[0][0]):
            cities_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            cities_markup.add(*[types.KeyboardButton(name[0]) for name in cities_result][:11])
            self.send_message(message.chat.id,
                              'По вашему запросу найден(ы) населенный(е) пункт(ы)😇\nВыберите один '
                              'из предложенных снизу или введите новый запрос.', reply_markup=cities_markup)
        elif len(cities_result) == 0:
            self.send_message(message.chat.id, 'Ошибка🤔 Не удалось найти совпадений в '
                                               'базе населенных пунктов, уточните запрос.')
        # the second call, when user chose required city
        else:
            sql.update_user_current_markup(message.from_user.id, 'forecasts_markup')
            sql.update_user_last_city(message.from_user.id, message.text)
            self.send_message(message.chat.id, 'Выберите, какой прогноз вас интересует? Либо вы можете запомнить '
                                               'этот населенный пункт (макс.: 3) для удобства.😏',
                              reply_markup=self.forecasts_markup)

    def check_count_of_user_cities(self, message, user_last_city):
        user_cities = sql.select_user_cities(message.from_user.id)
        if user_last_city in user_cities:
            self.send_message(message.chat.id, 'Упс...😬 Этот город уже сохранен!')
        elif len(user_cities) == 3:
            sql.update_user_current_markup(message.from_user.id, 'removing_markup')
            removing_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            cancel_button = types.KeyboardButton('Отмена')
            removing_markup.add(*[types.KeyboardButton(f'[❌] {name}') for name in user_cities])
            removing_markup.add(cancel_button)
            self.send_message(message.chat.id, f'Количество ваших сохраненных городов уже достигло максимума!😳 '
                                               f'Выберите, вместо какого населенного пункта вы хотите сохранить:'
                                               f' <b>{user_last_city}</b>',
                              reply_markup=removing_markup, parse_mode='html')
        else:
            self.remember_city(user_last_city, message, user_cities)

    def delete_city(self, message, user_last_city):
        city = message.text[4:]
        user_cities = sql.select_user_cities(message.from_user.id)
        try:
            user_cities.remove(city)
            updated_user_cities = '; '.join(user_cities)
            sql.update_user_cities(message.from_user.id, updated_user_cities)
            sql.update_user_current_markup(message.from_user.id, 'forecasts_markup')
            self.remember_city(user_last_city, message, user_cities)
        except Exception:
            self.send_message(message.chat.id, 'Воспользуйтесь кнопками!😡')

    def remember_city(self, user_last_city, message, user_cities):
        user_cities.append(user_last_city)
        updated_user_cities = '; '.join(user_cities)
        sql.update_user_cities(message.from_user.id, updated_user_cities)
        forecasts_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        today = types.KeyboardButton("Прогноз на сегодня")
        fc_for_5days = types.KeyboardButton('Прогноз на 5 дней')
        fc_for_10days = types.KeyboardButton('Прогноз на 10 дней')
        forecasts_markup.add(today, fc_for_5days, fc_for_10days)
        self.send_message(message.chat.id, '✏Город сохранен!) Выберете интересующий прогноз:',
                          reply_markup=forecasts_markup)

    # this function shows weather today and weather now
    def check_weather(self, message, user_last_city):
        url = sql.select_city_url(user_last_city)
        weather_now, time, temp_now, wind_day, wind_night, wind_dir_day, wind_dir_night, date, weather, night_temp, \
        day_temp, wind_now, wind_dir_now = parser.parse_weather(url)
        sql.update_user_current_markup(message.from_user.id, 'start_markup')
        # output
        self.send_message(message.chat.id,
                          f'🌤<b>Город опознан. Погода в населенном пункте {user_last_city.split(", ")[0]}:</b>\n'
                          f'\nСегодня: {date};\n'
                          f'\n{weather};\n'
                          f'\nТемпература ночью: {night_temp}°С'
                          f'\nТемпература днём: {day_temp}°С'
                          f'\nВетер ночью: {wind_night} м/с, <b>{wind_dir_night}</b>'
                          f'\nВетер днем: {wind_day} м/с, <b>{wind_dir_day}</b>\n'
                          f'\n⛈<b>Погода сейчас ({time}):</b>\n'
                          f'\n{weather_now};'
                          f'\nТемпература: {temp_now}°С'
                          f'\nВетер: {wind_now} м/с, <b>{wind_dir_now}</b>',
                          reply_markup=self.start_markup, parse_mode='html')

    # this function shows weather for 5 or for 10 days
    def check_weather_for_couple_days(self, user_last_city, message, num_of_days):
        url = sql.select_city_url(user_last_city)
        date, weather, day_temp, night_temp, wind, directions = parser.parse_weather_for_couple_days(url)

        output = f'<b>Погода в населенном пункте {user_last_city.split(", ")[0]} на {num_of_days} дней:</b>\n\n'
        for i in range(num_of_days):
            output += f'🔴<b>{date[i]}:</b> {weather[i]};\n' \
                      f'Макс. температура: {day_temp[i]};\n' \
                      f'Мин. температура: {night_temp[i]};\n' \
                      f'Макс. скорость ветра: {wind[i]}, <b>{directions[i]}</b>.\n\n'

        sql.update_user_current_markup(message.from_user.id, 'start_markup')
        self.send_message(message.chat.id, output, reply_markup=self.start_markup, parse_mode='html')


# creating telegram bot
bot = WeatherBot('YOUR_TELEGRAM_BOT_TOKEN')


@bot.message_handler(content_types='text')
def message_reply(message):
    user_id, user_name, user_nickname = message.from_user.id, message.from_user.first_name, message.from_user.username
    user_current_markup, user_last_city, user_city = sql.persoanalize_user(user_id, user_name, user_nickname)
    print(memory_usage())

    # this if-else operator processing user's requests and calls appropriate functions in WeatherBot class
    if message.text.lower() == 'узнать погоду' and user_current_markup == 'start_markup' or message.text == '/start':
        bot.start(message)

    elif message.text.lower() == 'отмена' and user_current_markup == 'removing_markup':
        sql.update_user_current_markup(message.from_user.id, 'forecasts_markup')
        bot.send_message(message.chat.id, 'Выберете интересующий прогноз:', reply_markup=bot.forecasts_markup)

    elif message.text.startswith('[❌] ') and user_current_markup == 'removing_markup':
        bot.delete_city(message, user_last_city)

    elif message.text.lower() == 'прогноз на сегодня' and user_current_markup == 'forecasts_markup':
        bot.check_weather(message, user_last_city)

    elif message.text.lower() == 'прогноз на 5 дней' and user_current_markup == 'forecasts_markup':
        bot.check_weather_for_couple_days(user_last_city, message, 5)

    elif message.text.lower() == 'прогноз на 10 дней' and user_current_markup == 'forecasts_markup':
        bot.check_weather_for_couple_days(user_last_city, message, 10)

    elif message.text.lower() == 'запомнить населенный пункт' and user_current_markup == 'forecasts_markup':
        bot.check_count_of_user_cities(message, user_last_city)

    elif user_current_markup == 'cities_markup':
        bot.check_city(message)

    else:
        bot.send_message(message.chat.id, 'Сообщение не распознано🤨 Пожалуйста, воспользуйтесь кнопками меню снизу, '
                                          'либо введите команду /start, чтобы вернуться в начало.')


bot.infinity_polling(timeout=10, long_polling_timeout=5)
