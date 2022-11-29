import requests
import re
from bs4 import BeautifulSoup
from itertools import groupby


def parse_schedule(link: str):
    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')

    rooms = dict()
    for room in get_all_rooms(soup):
        rooms[room] = dict()

    rows = get_all_rows(soup)
    rows_grouped_by_dates = group_rows_by_dates(rows)

    set_dates_for_rooms(rooms, rows_grouped_by_dates)

    return rooms


def get_all_rooms(html: BeautifulSoup):
    return [room.text for room in html.find_all('td', {'class': 'R1C2'})]


def get_all_rows(html: BeautifulSoup):
    return html.find_all('tr', {'class': re.compile(r'R\d+')})[2:-1]


def group_rows_by_dates(rows: list):
    it = iter([(k, list(group)) for k, group in groupby(rows, lambda row: row.find('td', {'class': re.compile(r'R\d+C0')}))])
    date_lessons = zip(it, it)
    return {x[0][0].text.strip(): x[0][1] + x[1][1] for x in date_lessons}


def set_dates_for_rooms(rooms: dict, rows_grouped_by_dates: dict):
    for date_group in rows_grouped_by_dates.items():
        init_room_date(rooms, date_group[0])

        for lessons_row in date_group[1]:
            lesson_number = get_lesson_number(lessons_row)
            set_lesson_names(rooms, lessons_row, lesson_number, date_group[0])


def init_room_date(rooms, date_group_key):
    for room_key in rooms:
        rooms[room_key][date_group_key] = dict()


def get_lesson_number(lessons_row):
    return lessons_row.find('td', {'class': re.compile(r'R\d+C1')}).text.replace('\xa0', ' ')


def set_lesson_names(rooms, lessons_row, lesson_number, date_group_key):
    i = 0
    room_keys = list(rooms)
    lesson_name_elements = lessons_row.find_all('td', {'class': re.compile(r'R\d+C2')})
    while i < len(rooms) and i < len(lesson_name_elements):
        rooms[room_keys[i]][date_group_key][lesson_number] = lesson_name_elements[i].text.replace('\xa0', ' ')
        i += 1
