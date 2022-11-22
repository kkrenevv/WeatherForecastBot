import psycopg2

host = 'localhost'
user = 'postgres'
password = 'YOUR_PASSWORD'
db_name = 'YOUR_DB_NAME'

connection = psycopg2.connect(host=host, user=user, password=password, database=db_name)
connection.autocommit = True


def select_city_name(city):
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT city_name FROM cities
                WHERE city_name LIKE '{city}%';'''
        )
        cities_result = cursor.fetchall()
    return cities_result


def select_city_url(user_last_city):
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT city_url FROM cities
                WHERE city_name LIKE '{user_last_city}%';'''
        )
        url = cursor.fetchone()[0]
    return url


def select_user_cities(user_id):
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT user_cities FROM users
                WHERE user_id = {user_id};'''
        )
        remembered_cities = cursor.fetchall()[0][0]

        if remembered_cities:
            return remembered_cities.split('; ')
        else:
            return []


def persoanalize_user(user_id, user_name, user_nickname):
    with connection.cursor() as cursor:
        cursor.execute(
            f'''SELECT user_current_markup, user_last_city, user_cities
                FROM users
                WHERE user_id = '{user_id}' '''
        )
        user_data = cursor.fetchall()

        if user_data:
            user_current_markup, user_last_city, user_city = user_data[0]
            return user_current_markup, user_last_city, user_city
        else:
            cursor.execute(
                f'''INSERT INTO users (user_id, user_name, user_nickname)
                    VALUES ({user_id}, '{user_name}', '{user_nickname}')'''
            )
            return None, None, None


def update_user_last_city(user_id, user_last_city):
    with connection.cursor() as cursor:
        cursor.execute(
            f'''UPDATE users
                SET user_last_city = '{user_last_city}'
                WHERE user_id = {user_id}'''
        )


def update_user_current_markup(user_id, new_markup):
    with connection.cursor() as cursor:
        cursor.execute(
            f'''UPDATE users
                SET user_current_markup = '{new_markup}'
                WHERE user_id = {user_id}'''
        )


def update_user_cities(user_id, new_cities):
    with connection.cursor() as cursor:
        cursor.execute(
            f'''UPDATE users
                SET user_cities = '{new_cities}'
                WHERE user_id = {user_id}'''
        )
# with connection.cursor() as cursor:
#     cursor.execute(
#         f'''SELECT city_url FROM cities
#             WHERE city_name LIKE '{message.text.capitalize()}%';'''
#     )
#     url = cursor.fetchone()
