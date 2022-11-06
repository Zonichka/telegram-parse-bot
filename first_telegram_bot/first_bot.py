import matplotlib as mpl
mpl.use('Agg')
import telebot
import requests
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fake_useragent import UserAgent
from bs4 import BeautifulSoup


class Country:
    def __init__(self, num, name, population, density, land_area):
        self.num = num
        self.name = name
        self.population = population
        self.density = density
        self.land_area = land_area


def write_to_csv(file, data):
    with open(file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Number', 'Name', 'Population', 'Density', 'Land_area'])
        for i in range(len(data)):
            writer.writerow(map(str, [data[i].num, data[i].name, data[i].population,
                            data[i].density, data[i].land_area]))


def parse_country(url):
    info = []
    info_country = []
    try:
        r = requests.get(url, headers={'User-Agent': UserAgent().chrome})
    except requests.exceptions.RequestException as e:
        return None
    soup = BeautifulSoup(r.content.decode('utf-8'), 'lxml')
    country_table = soup.find('table', attrs={'id': 'example2'})
    for tr in country_table.tbody.findAll('tr'):
        for td in tr:
            if td.string != ' ':
              info.append(td.string)

    for i in range(0, 1199, 12):
        buf = []
        for j in range(i, i+12):
            buf.append(info[j])
        info_country.append(Country(int(buf[0].replace(',', '')), buf[1], int(buf[2].replace(',', '')), int(buf[5].replace(',', '')),  int(buf[6].replace(',', ''))))
    return info_country


def histograms(data):
    pop = []
    den = []
    land = []

    for i in data:
        pop.append(i.population)
        den.append(i.density)
        land.append(i.land_area)

    fig1, pop_hist = plt.subplots()
    fig2, den_hist = plt.subplots()
    fig3, land_hist = plt.subplots()

    pop_hist.hist(pop, 300)
    den_hist.hist(den)
    land_hist.hist(land)

    fig1.set_figwidth(12)
    fig1.set_figheight(6)
    pop_hist.set_title("population chart bar")
    den_hist.set_title("density chart bar")
    land_hist.set_title("land area chart bar")

    fig1.savefig('pop_hist.png')
    fig2.savefig('den_hist.png')
    fig3.savefig('land_hist.png')


def sort_by_parameter(data, param):
    if param == "Population":
        return sorted(data, key=lambda data: data.population)
    if param == "Density":
        return sorted(data, key=lambda data: data.density)
    if param == "Land area":
        return sorted(data, key=lambda data: data.land_area)


bot = telebot.TeleBot('1116071327:AAFsPolL2p3a6G_v1aWMd88e9MZsmZNh1Ac')

keyboard_function = telebot.types.ReplyKeyboardMarkup()
keyboard_function.row('Гистограмма', 'Сортировка')

keyboard_sort = telebot.types.ReplyKeyboardMarkup()
keyboard_sort.row('Land area', 'Population', 'Density')

string_start = """Привет, я бот, который работает с сайтом https://www.worldometers.info по населению.
Я собираю различную статистическую информацию за 2020 год.
Набери '/help', чтобы узнать, что я умею. """
string_help = """Введите '/parse', чтобы начать собирать данные о 100 стран с наибольшим населением в мире.
После того, как бот выведет 'Бот собрал данные' можем сделать сделать следующие действия:
1) Построить гистограммы стран
2) Отсортировать страны по выбранному параметру
Вывести все 100 стран - 'csv_table'. 
"""


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, string_start)


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, string_help)


@bot.message_handler(commands=['parse'])
def parse_message(message):
    bot.send_message(message.chat.id, "Начинаем парсить")
    info_country = parse_country('https://www.worldometers.info/world-population/population-by-country/')
    if info_country is None:
        bot.send_message(message.chat.id, "Не удалось (")
        return
    write_to_csv('country_table.csv', info_country)
    bot.send_message(message.chat.id, "Бот собрал данные")
    msg = bot.reply_to(message, "Теперь, выберите, что вы хотите сделать с полученной таблицой:",
                 reply_markup=keyboard_function)
    bot.register_next_step_handler(msg, process_answer)


def csv_parse(file):
    info_country = []
    with open(file, 'r') as f:
        lines = f.readlines()
    for i in lines[1:]:
        buf = i.split(',')
        info_country.append(Country(int(buf[0]), buf[1], int(buf[2]), int(buf[3]),  int(buf[4])))
    return info_country


def process_answer(msg):
    if msg.text == 'Гистограмма':
        histograms(csv_parse('country_table.csv'))
        with open('den_hist.png', 'rb') as f1:
            bot.send_document(msg.chat.id, f1)
        with open('land_hist.png', 'rb') as f2:
            bot.send_document(msg.chat.id, f2)
        with open('pop_hist.png', 'rb') as f3:
            bot.send_document(msg.chat.id, f3)
    elif msg.text == 'Сортировка':
        msg1 = bot.reply_to(msg, "Выберите параметр сортировки:", reply_markup=keyboard_sort)
        bot.register_next_step_handler(msg1, process_sort)


def process_sort(msg):
    sorted = sort_by_parameter(csv_parse('country_table.csv'), msg.text)
    write_to_csv('sorted.csv', sorted)
    with open('sorted.csv', 'rb') as f:
        bot.send_document(msg.chat.id, f)


@bot.message_handler(commands=['csv_table'])
def table_message(message):
    with open('country_table.csv', 'rb') as table_csv:
        bot.send_document(message.chat.id, table_csv)


bot.infinity_polling(True)
