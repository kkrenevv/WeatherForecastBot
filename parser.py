from bs4 import BeautifulSoup as BS
import requests

headers = {'accept': '*/*',
           'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/101.0.4951.67 Safari/537.36'}


def parse_weather(url):
    re = requests.get(url, headers=headers)
    re_text = re.text
    sup = BS(re_text, 'lxml')

    # weather now
    weather_now = sup.find('a', class_='weathertab weathertab-link tooltip').get("data-text").strip()
    time = sup.find('a', class_='weathertab weathertab-link tooltip').find('div', class_='day').text.strip()
    temp_now = sup.find('a', class_='weathertab weathertab-link tooltip'). \
        find('span', class_='unit unit_temperature_c').text.strip()

    # wind today
    wind_day = sup.find('div', class_="widget-row widget-row-wind-speed").find_all(
        class_="row-item")[4].find(class_="wind-unit unit unit_wind_m_s").text.strip()
    wind_night = sup.find('div', class_="widget-row widget-row-wind-speed").find_all(
        class_="row-item")[0].find(class_="wind-unit unit unit_wind_m_s").text.strip()
    wind_dir_day = sup.find('div', class_="widget-row widget-row-wind-direction").find_all(class_="row-item")[4] \
        .text.strip()
    if not wind_dir_day:
        wind_dir_day = '-'
    wind_dir_night = sup.find('div', class_="widget-row widget-row-wind-direction").find_all(class_="row-item")[0] \
        .text.strip()
    if not wind_dir_night:
        wind_dir_night = '-'

    # weather today
    date = sup.find('a', class_='weathertab weathertab-block tooltip').find('div', class_='tab-content') \
        .find('div').text.strip()
    weather = sup.find('a', class_='weathertab weathertab-block tooltip').get("data-text").strip()
    night_temp = sup.find('a', class_='weathertab weathertab-block tooltip').find_all(
        'div', class_='value')[0].find(class_="unit unit_temperature_c").text.strip()
    day_temp = sup.find('a', class_='weathertab weathertab-block tooltip').find_all('div', class_='value')[1].find(
        class_="unit unit_temperature_c").text.strip()

    # wind now
    html = requests.get(url + 'now/', headers=headers)
    sup = BS(html.text, 'lxml')
    wind_now = sup.find('div', class_="now-info").find('div', class_="unit unit_wind_m_s").contents[0].text.strip()
    wind_dir_now = sup.find('div', class_="unit unit_wind_m_s").contents[1].text
    if len(wind_dir_now.split()) <= 1:
        wind_dir_now = '-'
    else:
        wind_dir_now = wind_dir_now.split()[1]
    return weather_now, time, temp_now, wind_day, wind_night, wind_dir_day, wind_dir_night, date, weather, night_temp,\
           day_temp, wind_now, wind_dir_now


def parse_weather_for_couple_days(url):
    # forming get request
    html = requests.get(url + '10-days/', headers=headers)
    sup = BS(html.text, 'lxml')

    # weather for 5-10 days
    date = [i.contents[0].text.strip() + ', ' + i.contents[1].text.strip().split()[0] for i in
            sup.find(class_="widget-row widget-row-days-date").find_all('a')]
    weather = [i.get('data-text').strip() for i in
               sup.find(class_="widget-row widget-row-icon").find_all('div', class_="weather-icon tooltip")]
    day_temp = [i.contents[0].text.strip() for i in sup.find('div', class_="values").find_all(class_="maxt")]
    night_temp = [i.contents[0].text.strip() for i in sup.find('div', class_="values").find_all(class_="mint")]
    wind = [i.text.split()[0].strip() for i in
            sup.find(class_="widget-row widget-row-wind-gust row-with-caption").find_all(class_="row-item")]
    directions = [i.text.strip() for i in sup.find(class_="widget-row widget-row-wind-direction").find_all(
        class_="row-item")]
    return date, weather, day_temp, night_temp, wind, directions
