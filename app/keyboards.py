from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import request
#from app.database.requests import get_categories, get_cards_by_category


menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Создать заявку')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Начните создание заявки...')

who_kb = InlineKeyboardMarkup(inline_keyboard=[
                              [InlineKeyboardButton(text='Заказчик', callback_data='who_zakazcik')],
                              [InlineKeyboardButton(text='Перевозчик', callback_data='who_trans')]
                              ])

logo_kb = InlineKeyboardMarkup(inline_keyboard=[
                              [InlineKeyboardButton(text='Да', callback_data='logo_Y')],
                              [InlineKeyboardButton(text='Нет', callback_data='logo_N')]
                              ])

zaia_kb = InlineKeyboardMarkup(inline_keyboard=[
                              [InlineKeyboardButton(text='Заявка', callback_data='zaya_Заявка')],
                              [InlineKeyboardButton(text='Договор-Заявка', callback_data='zaya_Договор-Заявка')]
                              ])

data_kb = ReplyKeyboardMarkup(keyboard=[
                              [KeyboardButton(text='Сегодняшняя дата')],
                              ],
                                resize_keyboard=True,
                                input_field_placeholder='Введите дату или нажмите кнопку чтоб ввести сегодняшнюю'
                                )

space_kb = ReplyKeyboardMarkup(keyboard=[
                                [KeyboardButton(text='С начала'),
                                KeyboardButton(text='Пропустить')]
                              ],
                                resize_keyboard=True

                                )


z_v_kb = ReplyKeyboardMarkup(keyboard=[
                                [KeyboardButton(text='Добавить_Погрузка')],
                                [KeyboardButton(text='Добавить_Выгрузка')]
                              ],
                                resize_keyboard=True,
                                input_field_placeholder='Выберите тип точки или закончите формирование маршрута'

                                )

z_vlast_kb = ReplyKeyboardMarkup(keyboard=[
                                [KeyboardButton(text='Добавить_Погрузка')],
                                [KeyboardButton(text='Добавить_Выгрузка')],
                                [KeyboardButton(text='Это была последняя точка')]
                              ],
                                resize_keyboard=True,
                                input_field_placeholder='Выберите тип точки или закончите формирование маршрута'

                                )

stake_kb = InlineKeyboardMarkup(inline_keyboard=[
                              [InlineKeyboardButton(text='с НДС', callback_data='NDS_НДС')],
                              [InlineKeyboardButton(text='без НДС', callback_data='NDS_Без НДС')],
                              [InlineKeyboardButton(text='НДС = 0', callback_data='NDS_НДС равен 0')],
                              [InlineKeyboardButton(text='Наличные', callback_data='NDS_Наличные')]
                              ],)

curency_kb = ReplyKeyboardMarkup(keyboard=[
                                [KeyboardButton(text='Руб'),
                                KeyboardButton(text='Доллар'),
                                KeyboardButton(text='Евро'),
                                KeyboardButton(text='Юань'),
                                KeyboardButton(text='Тенге')]
                              ],
                                resize_keyboard=True,
                                input_field_placeholder='Выберите Валюту')

cond_kb = ReplyKeyboardMarkup(keyboard=[
                                [KeyboardButton(text='С начала'),
                                KeyboardButton(text='Стандартные условия')]
                              ],
                                resize_keyboard=True

                                )


