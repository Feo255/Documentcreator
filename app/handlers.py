import os
import asyncio
from datetime import datetime


from app.config import bot
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, StateFilter

from aiogram.types import Message, CallbackQuery, BufferedInputFile, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
#from aiogram.utils import executor
from app.dadata_Int import get_company_info_by_inn
import app.keyboards as kb
from app.keyboards import logo_kb
from dotenv import load_dotenv

from app.models.generator import generate_pdf
from app.parsing import wrap_sentences_in_li
from app.models.stamp import stamp_parsing



load_dotenv()

client = Router()
SAVE_DIR = 'models'

@client.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
        await message.answer("Вас приветствует бот для создания заявок на перевозку\n\n"
                             "Нажмите кнопку внизу, чтобы начать процесс создания заявки",
                             reply_markup=kb.menu)

@client.message(F.text == 'С начала')
async def start_pr(message: Message, state: FSMContext):
    await state.clear()
    await cmd_start(message, state)

@client.message(F.text == 'Создать заявку')
async def start_pr(message: Message, state: FSMContext):

    await message.answer('.',
                         reply_markup=ReplyKeyboardRemove())
    await message.answer('Вы являетесь заказчиком или первозчиком',
                         reply_markup=kb.who_kb)
    await state.set_state('reg_who')

@client.callback_query(F.data.startswith('who_'))
async def who_(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    who_is = callback.data.split('_')[1]
    await state.update_data(who=who_is)
    await callback.message.edit_text('Вы будете загружать логотип вашей компании?',
                                     reply_markup=logo_kb)

@client.callback_query(F.data == 'logo_N')
async def logo_N(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await callback.message.edit_text('Заявка или договор-заявка?',
                                     reply_markup=kb.zaia_kb)
    await state.update_data(logo_=' ')
    data = await state.get_data()
    print(data)

@client.callback_query(F.data == 'logo_Y')
async def start_upload_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    await callback.message.edit_text("Пожалуйста, отправьте изображение для загрузки.")
    await state.set_state('reg_logo')

def setup_handlers(dp: Dispatcher, bot: Bot):
    @client.message(StateFilter('reg_logo'))
    async def handle_photo(message: Message, state: FSMContext):
        if bot is None:
            print("Bot еще не инициализирован")
            return

        photo = message.photo[-1]
        print(photo)
        print(photo.file_id)
        print(photo.file_unique_id)
        # Получаем объект File через bot.get_file()
        file = await bot.get_file(photo.file_id)
        filename = os.path.basename(file.file_path)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir =os.path.join(base_dir, 'models')
        #save_dir = r'C:\Users\synesis1\PycharmProjects\BotLogist\.venv\app\models'
        save_path = os.path.join(save_dir, filename)
        await bot.download_file(file.file_path, save_path)

        await state.update_data(logo_=filename)
        await message.answer('Заявка или договор-заявка?',
                                     reply_markup=kb.zaia_kb)
        data = await state.get_data()
        print(data)




@client.callback_query(F.data.startswith('zaya_'))
async def zaya_(callback: CallbackQuery, state: FSMContext):


    await callback.answer('')
    zaia = callback.data.split('_')[1]
    zaia_2 = zaia[:-1]+'у'
    await state.update_data(zaiavka=zaia, zaiavka_2=zaia_2.lower())
    await callback.message.edit_text(f'Введите номер заявки\nТолько цифры')
    data = await state.get_data()
    print(data)
    await state.set_state('reg_number')

@client.message(StateFilter('reg_zaiavka'))
async def not_digit(message: Message, state: FSMContext):
    await message.answer('Номер содержал не только цифры.\nВведите номер ещё раз',
                             reply_markup=ReplyKeyboardRemove())
    await state.set_state('reg_number')

@client.message(StateFilter('reg_number'))
async def number_(message: Message, state: FSMContext):
    number = message.text
    print(number)
    if number.isdigit():
        await state.update_data(number=number)
        data = await state.get_data()
        print(data)
        await message.answer('Введите дату в формате дд.мм.гггг или используйте сегодяшнюю',
                             reply_markup=kb.data_kb)
        await state.set_state('reg_data')
    else:
        print('here')
        await state.set_state('reg_zaiavka')
        await not_digit(message, state)


@client.message(F.text == 'Сегодняшняя дата', StateFilter('reg_data'))
async def data_(message: Message, state: FSMContext):
    now = datetime.now()

    # Format date as dd,mm,yyyy
    formatted_date = now.strftime("%d.%m.%Y")
    await state.update_data(data_=str(formatted_date))
    await message.answer('Введите ИНН заказчика',
                             reply_markup=ReplyKeyboardRemove())
    await state.set_state('reg_INN_Z')

@client.message(StateFilter('reg_data'))
async def data__(message: Message, state: FSMContext):
#Нужно добавить проверку по формату ввода и по содержимому
    formatted_date = message.text

    await state.update_data(data_=str(formatted_date))
    await message.answer('Введите ИНН заказчика',
                             reply_markup=ReplyKeyboardRemove())
    await state.set_state('reg_INN_Z')

@client.message(StateFilter('reg_INN_Z'))
async def inn_z(message: Message, state: FSMContext):
    current_state = await state.get_state()
    print(f"Текущее состояние: {current_state}")

    INN_Z = message.text
    if INN_Z.isdigit() and len(INN_Z) in (10, 12):
        adata = await get_company_info_by_inn(INN_Z)
        if adata is None:
            await message.answer("Данные компании не обнаружены.\n"
                                 "Проверьте правильность ИНН заказчика и посторите ввод.")
            await state.set_state('reg_INN_Z')
        elif adata is str:
            await message.answer(f"Ошибка работы сервиса adata {adata}.\n"
                                 "Проверьте правильность ИНН заказчика и посторите ввод.\n"
                                 "Если ошибка повторяется обратитесь за помошью в службу поддержки")
            await state.set_state('reg_INN_Z')
        else:
            if adata['kpp'] == ' ':
                ustav = 'свидетельства о государственной регистрации'
            else:
                ustav = 'устава'
            await state.update_data(INN_Z=INN_Z, ogrn_z=adata['ogrn'], kpp_z=adata['kpp'], full_z=adata['full'], short_z=adata['short'],
                                    full_address_z=adata['full_address'], surname_z=adata['f_surname'], name_z=adata['f_name'],
                                    patronymic_z=adata['f_patronymic'], position_z=adata['position'], sh_name_z=adata['sh_name'], ustav_z=ustav)
            await message.answer(f'Получены данные {adata['full']}')
            await message.answer('Введите Расчётный счёт заказчика',
                            reply_markup=kb.space_kb)
            await state.set_state('reg_RS_Z')
    else:
        await message.answer("Некорректный ввод. Введите ИНН заказчика.")
        await state.set_state('reg_INN_Z')

@client.message(StateFilter('reg_RS_Z'))
async def rs_z(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    RS_Z = message.text
    if RS_Z == "Пропустить":
        await state.update_data(RS_Z=' ')
        await message.answer('Введите кор счёт заказчика',
                         reply_markup=kb.space_kb)
        await state.set_state('reg_KS_Z')
    else:
#Здесь проверки что это это цифры
        await state.update_data(RS_Z=RS_Z)
        await message.answer('Введите кор счёт заказчика',
                         reply_markup=kb.space_kb)
        await state.set_state('reg_KS_Z')

@client.message(StateFilter('reg_KS_Z'))
async def ks_z(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    KS_Z = message.text
    if KS_Z == "Пропустить":
        await state.update_data(KS_Z=' ')
        await message.answer('Введите БИК банка заказчика',
                         reply_markup=kb.space_kb)
        await state.set_state('reg_BIK_Z')
    else:
#Здесь проверки что это это цифры
        await state.update_data(KS_Z=KS_Z)
        await message.answer('Введите БИК банка заказчика',
                         reply_markup=kb.space_kb)
        await state.set_state('reg_BIK_Z')


@client.message(StateFilter('reg_BIK_Z'))
async def bik_z(message: Message, state: FSMContext):

    BIK_Z = message.text

    if BIK_Z == "Пропустить":
        await state.update_data(BIK_Z=' ')
        await message.answer('Введите имя контактного лица заказчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_cont_z')
    else:
#Здесь проверки что это это цифры
        await state.update_data(BIK_Z=BIK_Z)
        data = await state.get_data()
        print(data)
        await message.answer('Введите имя контактного лица заказчика',
                     reply_markup=kb.space_kb)
        await state.set_state('reg_cont_z')

@client.message(StateFilter('reg_cont_z'))
async def cont_z(message: Message, state: FSMContext):

    cont_z = message.text

    if cont_z == "Пропустить":
        await state.update_data(cont_z=' ')
        await message.answer('Введите номер телефона контактного лица заказчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_cont_z_tel')
    else:
#Здесь проверки что это это цифры
        await state.update_data(cont_z=cont_z)
        data = await state.get_data()
        print(data)
        await message.answer('Введите номер телефона контактного лица заказчика',
                     reply_markup=kb.space_kb)
        await state.set_state('reg_cont_z_tel')

@client.message(StateFilter('reg_cont_z_tel'))
async def cont_tel_z(message: Message, state: FSMContext):

    cont_z_tel = message.text

    if cont_z_tel == "Пропустить":
        await state.update_data(cont_z_tel=' ')
        await message.answer('Введите email контактного лица заказчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_cont_z_email')
    else:
#Здесь проверки что это это цифры
        await state.update_data(cont_z_tel=cont_z_tel)
        data = await state.get_data()
        print(data)
        await message.answer('Введите email контактного лица заказчика',
                     reply_markup=kb.space_kb)
        await state.set_state('reg_cont_z_email')
        
@client.message(StateFilter('reg_cont_z_email'))
async def cont_email_z(message: Message, state: FSMContext):

    cont_z_email = message.text

    if cont_z_email == "Пропустить":
        await state.update_data(cont_z_email=' ')
        await message.answer('Введите почтовый адреc заказчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_post_z')
    else:

        await state.update_data(cont_z_email=cont_z_email)
        data = await state.get_data()
        print(data)
        await message.answer('Введите почтовый адреc заказчика',
                     reply_markup=kb.space_kb)
        await state.set_state('reg_post_z')

@client.message(StateFilter('reg_post_z'))
async def post_zz(message: Message, state: FSMContext):
    post_z = message.text

    if post_z == "Пропустить":
        await state.update_data(post_z=' ')
        await message.answer('Введите ИНН перевозчика',
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state('reg_INN_P')
    else:
        # Здесь проверки что это это цифры
        await state.update_data(post_z=post_z)
        data = await state.get_data()
        print(data)

        await message.answer('Введите ИНН перевозчика',
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state('reg_INN_P')

@client.message(StateFilter('reg_INN_P'))
async def inn_p(message: Message, state: FSMContext):
    

    INN_P = message.text
    if INN_P.isdigit() and len(INN_P) in (10, 12):
        adata = await get_company_info_by_inn(INN_P)
        if adata is None:
            await message.answer("Данные компании не обнаружены.\n"
                                 "Проверьте правильность ИНН заказчика и посторите ввод.")
            await state.set_state('reg_INN_P')
        elif adata is str:
            await message.answer(f"Ошибка работы сервиса adata {adata}.\n"
                                 "Проверьте правильность ИНН заказчика и посторите ввод.\n"
                                 "Если ошибка повторяется обратитесь за помошью в службу поддержки")
            await state.set_state('reg_INN_P')
        else:
            if adata['kpp'] == ' ':
                ustav = 'свидетельства о государственной регистрации'
            else:
                ustav = 'устава'
            await state.update_data(INN_P=INN_P, ogrn_p=adata['ogrn'], kpp_p=adata['kpp'], full_p=adata['full'], short_p=adata['short'],
                                    full_address_p=adata['full_address'], surname_p=adata['f_surname'], name_p=adata['f_name'],
                                    patronymic_p=adata['f_patronymic'], position_p=adata['position'], sh_name_p=adata['sh_name'], ustav_p=ustav)
            await message.answer(f'Получены данные {adata['full']}')
            await message.answer('Введите Расчётный счёт заказчика',
                            reply_markup=kb.space_kb)
            await state.set_state('reg_RS_P')

    else:
        await message.answer("Некорректный ввод. Введите ИНН перевозчика.")
        await state.set_state('reg_INN_P')

@client.message(StateFilter('reg_RS_P'))
async def rs_p(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    RS_P = message.text
    if RS_P == "Пропустить":
        await state.update_data(RS_P=' ')
        await message.answer('Введите кор счёт перевозчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_KS_P')
    else:
#Здесь проверки что это это цифры
        await state.update_data(RS_P=RS_P)
        await message.answer('Введите кор счёт перевозчика',
                         reply_markup=kb.space_kb)
        await state.set_state('reg_KS_P')

@client.message(StateFilter('reg_KS_P'))
async def ks_p(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)

    KS_P = message.text
    if KS_P == "Пропустить":
        await state.update_data(KS_P=' ')
        await message.answer('Введите БИК банка перевозчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_BIK_P')
    else:
#Здесь проверки что это это цифры
        await state.update_data(KS_P=KS_P)
        await message.answer('Введите БИК банка перевозчика',
                         reply_markup=kb.space_kb)
        await state.set_state('reg_BIK_P')


@client.message(StateFilter('reg_BIK_P'))
async def bik_p(message: Message, state: FSMContext):

    BIK_P = message.text
    if BIK_P == "Пропустить":
        await state.update_data(BIK_P=' ')
        await message.answer('Введите имя контактного лица перевозчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_cont_p')
    else:
        await state.update_data(BIK_P=BIK_P)
        data = await state.get_data()
        print(data)
        await message.answer('Введите имя контактного лица перевозчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_cont_p')


@client.message(StateFilter('reg_cont_p'))
async def cont_p(message: Message, state: FSMContext):
    cont_p = message.text

    if cont_p == "Пропустить":
        await state.update_data(cont_p=' ')
        await message.answer('Введите номер телефона контактного перевозчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_cont_p_tel')
    else:
        # Здесь проверки что это это цифры
        await state.update_data(cont_p=cont_p)
        data = await state.get_data()
        print(data)
        await message.answer('Введите номер телефона контактного перевозчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_cont_p_tel')


@client.message(StateFilter('reg_cont_p_tel'))
async def cont_tel_p(message: Message, state: FSMContext):
    cont_p_tel = message.text

    if cont_p_tel == "Пропустить":
        await state.update_data(cont_p_tel=' ')
        await message.answer('Введите email контактного лица перевозчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_cont_p_email')
    else:
        # Здесь проверки что это это цифры
        await state.update_data(cont_p_tel=cont_p_tel)
        data = await state.get_data()
        print(data)
        await message.answer('Введите email контактного лица перевозчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_cont_p_email')


@client.message(StateFilter('reg_cont_p_email'))
async def cont_email_p(message: Message, state: FSMContext):
    cont_p_email = message.text

    if cont_p_email == "Пропустить":
        await state.update_data(cont_p_email=' ')
        await message.answer('Введите почтовый адреc перевозчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_post_p')
    else:

        await state.update_data(cont_p_email=cont_p_email)
        data = await state.get_data()
        print(data)
        await message.answer('Введите почтовый адреc перевозчика',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_post_p')

@client.message(StateFilter('reg_post_p'))
async def post_pp(message: Message, state: FSMContext):
    post_p = message.text

    if post_p == "Пропустить":
        await state.update_data(post_p=' ')
        await message.answer('Загрузите фото вашей подписи (Факсимилию)',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_fax')
    else:
        # Здесь проверки что это это цифры
        await state.update_data(post_p=post_p)
        data = await state.get_data()
        print(data)
        await message.answer('Загрузите фото вашей подписи (Факсимилию)',
                             reply_markup=kb.space_kb)
        await state.set_state('reg_fax')


def setup_handlers2(dp: Dispatcher, bot: Bot):
    @client.message(StateFilter('reg_fax'))
    async def handle_photo(message: Message, state: FSMContext):
        if not message.photo:
            await state.update_data(fax=' ')
            await message.answer('Загрузите вашу печать',
                                 reply_markup=kb.space_kb)
            await state.set_state('reg_stamp')
            data = await state.get_data()
            print(data)
        else:
            if bot is None:
                print("Bot еще не инициализирован")
                return

            photo = message.photo[-1]
            print(photo)
            print(photo.file_id)
            print(photo.file_unique_id)
            # Получаем объект File через bot.get_file()
            fax = await bot.get_file(photo.file_id)
            filename = os.path.basename(fax.file_path)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            save_dir = os.path.join(base_dir, 'models')
            #save_dir = r'C:\Users\synesis1\PycharmProjects\BotLogist\.venv\app\models'
            save_path = os.path.join(save_dir, filename)
            await bot.download_file(fax.file_path, save_path)

            await state.update_data(fax=filename)
            await message.answer('Загрузите вашу печать',
                                 reply_markup=kb.space_kb)
            await state.set_state('reg_stamp')
            data = await state.get_data()
            print(data)
        
def setup_handlers3(dp: Dispatcher, bot: Bot):
    @client.message(StateFilter('reg_stamp'))
    async def handle_photo(message: Message, state: FSMContext):
        if not message.photo:
            await state.update_data(stamp=' ')
            await state.update_data(i=0)
            await state.update_data(zv='Погрузка')
            await state.update_data(track=f'<td>')
            await state.update_data(loading=f'<tr>')
            await message.answer('Введите адрес загрузки \n''через запятую\n''Страна, область, город, улица, номер дома',
                                 reply_markup=ReplyKeyboardRemove())
            await state.set_state('reg_loading')
            data = await state.get_data()
            print(data)
        else:
            if bot is None:
                print("Bot еще не инициализирован")
                return

            photo = message.photo[-1]
            print(photo)
            print(photo.file_id)
            print(photo.file_unique_id)
            # Получаем объект File через bot.get_file()
            fax = await bot.get_file(photo.file_id)
            filename = os.path.basename(fax.file_path)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            save_dir = os.path.join(base_dir, 'models')
            #save_dir = r'C:\Users\synesis1\PycharmProjects\BotLogist\.venv\app\models'
            save_path = os.path.join(save_dir, filename)
            remove_file = filename
            await bot.download_file(fax.file_path, save_path)
            print(filename)
            filename = stamp_parsing(save_path)
            print(filename)
            await state.update_data(i=0)
            delete_path = os.path.join(save_dir, remove_file)

            await state.update_data(stamp=filename)

            os.remove(delete_path)

            await state.update_data(zv='Погрузка')
            await state.update_data(track=f'<td>')
            await state.update_data(loading=f'<tr>')
            await message.answer('Введите адрес загрузки \n''через запятую\n''Страна, область, город, улица, номер дома',
                                 reply_markup=ReplyKeyboardRemove())

            await state.set_state('reg_loading')

            data = await state.get_data()
            print(data)

@client.message(F.text.startswith('Добавить_'))
async def loading_start2(message: Message, state: FSMContext):
    zv = message.text.split('_')[1]
    await state.update_data(zv=zv)
    await message.answer('Введите адрес загрузки \n''через запятую\n''Страна, область, город, улица, номер дома')

    await state.set_state('reg_loading')

@client.message(StateFilter('reg_loading'))
async def loading_start(message: Message, state: FSMContext):
    try:


        loading = message.text
        loading_s = loading.split(',')
#Здесь проверки
        address_c, address_r, address_g, address_s, address_h = loading_s

        data = await state.get_data()
        zv=data['zv']
        track = data['track']
        loading_old = data['loading']
        i = data['i']
        i = i + 1
        await state.update_data(i=i)

        await state.update_data(track=f'{track}г.{address_g} ({address_r}), {address_c}-')
        await state.update_data(loading=f'{loading_old}<th>Пункт{i}<br>{zv}</th><td><b>Адрес:</b>{address_s}{address_h}')

        data = await state.get_data()
        print(data)
        await message.answer('Введите дату и время (начала и конца) погрузки\n''Формат: дд.мм.гггг с чч:мм по чч:мм ')
        await state.set_state('reg_loadtime')
    except:
        await message.answer('Некорректный ввод Повторите пожалуйста\n''Обратите внимение что должно быть 5 слов через запятую\n''Страна, область, город, улица, номер дома')
        await state.set_state('reg_loading')



@client.message(StateFilter('reg_loadtime'))
async def loading_data(message: Message, state: FSMContext):
    data = await state.get_data()
    loading = data['loading']
    loaddata = message.text
#Здесь проверки

    await state.update_data(loading=f'{loading}<br><b>Дата:</b>{loaddata}')
    data = await state.get_data()
    print(data)
    await message.answer('Укажите способ загузки/выгрузки'
                             )
    await state.set_state('reg_loadway')

@client.message(StateFilter('reg_loadway'))
async def loading_way(message: Message, state: FSMContext):
    data = await state.get_data()
    loading = data['loading']
    loadway = message.text
#Здесь проверки

    await state.update_data(loading=f'{loading}<br><b>Способ погрузки:</b>{loadway}')
    data = await state.get_data()
    print(data)
    await message.answer('Укажите укажите название груза / вес / объём (если надо д/ш/в)'
                             )
    await state.set_state('reg_loadtype')

@client.message(StateFilter('reg_loadtype'))
async def loading_type(message: Message, state: FSMContext):
    data = await state.get_data()
    loading = data['loading']
    loadtype = message.text
#Здесь проверки

    await state.update_data(loading=f'{loading}<br><b>Груз/параметры:</b>{loadtype}</td></tr>')
    data = await state.get_data()
    print(data)
    if data['i'] < 2:
        await message.answer('Выберите следующую точку маршрута',
                             reply_markup=kb.z_v_kb)




    else:
        await message.answer('Выберите следующую точку маршрута',
                             reply_markup=kb.z_vlast_kb)
        await state.set_state('reg_NDS')

@client.message(F.text == 'Это была последняя точка')
async def stake_select(message: Message, state: FSMContext):
    data = await state.get_data()
    track = data['track']
    await state.update_data(track=f'{track}</td>')
    await message.answer('Выберите тип ставки',
                         reply_markup=kb.stake_kb)


@client.callback_query(F.data.startswith('NDS_'))
async def stake_type(callback: CallbackQuery, state: FSMContext):
    await callback.answer('')
    nds = callback.data.split('_')[1]
    await state.update_data(nds=nds)

    await callback.message.answer('Введите Ставку',
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state('reg_stake')

@client.message(StateFilter('reg_stake'))
async def stake(message: Message, state: FSMContext):
    stake_nb = message.text
    await state.update_data(stake_nb=stake_nb)
    await message.answer('Выберите валюту',
                         reply_markup=kb.curency_kb)
    await state.set_state('reg_cur')

@client.message(StateFilter('reg_cur'))
async def stake_fin(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    stake_cur = message.text
    stake_sum = data['stake_nb']
    nds = data['nds']
    if nds == 'НДС':
        await state.update_data(stake=f'{stake_sum} {stake_cur}. Безналичный расчет, в т.ч. НДС.<br> Условия оплаты: ')
    elif nds == 'Без НДС':
        await state.update_data(
            stake=f'{stake_sum} {stake_cur}. Безналичный расчет.<br> Условия оплаты: ')
    elif nds == 'NDS_НДС равен 0':
        await state.update_data(
            stake=f'{stake_sum} {stake_cur}. Безналичный расчет.<br> Условия оплаты: ')
    else:
        await state.update_data(
            stake=f'{stake_sum} {stake_cur}. Наличный расчет.<br> Условия оплаты: ')
    await message.answer('Введите условия оплаты',
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state('reg_pay')

@client.message(StateFilter('reg_pay'))
async def drivername(message: Message, state: FSMContext):
    pay = message.text
    data = await state.get_data()
    stake_old = data['stake']
    await state.update_data(stake=f'{stake_old}{pay}')
    await message.answer('Введите Имя фамилию и отчество водителя')
    await state.set_state('reg_drivername')


@client.message(StateFilter('reg_drivername'))
async def drivername(message: Message, state: FSMContext):
    drivername = message.text
    await state.update_data(drivername=drivername)
    await message.answer('Введите номер телефона водителя')
    await state.set_state('reg_driverphone')

@client.message(StateFilter('reg_driverphone'))
async def drivername(message: Message, state: FSMContext):
    driverphone = message.text
    await state.update_data(driverphone=driverphone)
    await message.answer('Введите данные водительского удостоверения \n'
                         'серия, номер, кем выдан, дата выдачи')
    await state.set_state('reg_driverlicence')


@client.message(StateFilter('reg_driverlicence'))
async def drivelicence(message: Message, state: FSMContext):
    driverlicence = message.text
    await state.update_data(driverlicence=driverlicence)
    await message.answer('Введите данные паспорта водителя \n'
                             'серия, номер, кем выдан, дата выдачи')
    await state.set_state('reg_driverpassport')

@client.message(StateFilter('reg_driverpassport'))
async def drivelicence(message: Message, state: FSMContext):
    driverpassport = message.text
    await state.update_data(driverpassport=driverpassport)
    await message.answer('Введите данные Транспортного средства \n'
                         'Марка, гос номер, прицеп, тип, грузоподъёмность')
    await state.set_state('reg_car')

@client.message(StateFilter('reg_car'))
async def drivelicence(message: Message, state: FSMContext):
    car = message.text
    await state.update_data(car=car)
    await message.answer('Введите права и обязанности сторон',
                         reply_markup=kb.cond_kb)
    await state.set_state('reg_conditions')

    


#@client.message(StateFilter('reg_conditions'))
#async def conditions(message: Message, state: FSMContext):
#    await state.update_data(conditions=message.text)
#   data = await state.get_data()
#    pdf_bytes = generate_pdf(data)
#    file = BufferedInputFile(pdf_bytes, filename="contract.pdf")
#    await message.answer_document(file)
#    await state.clear()

@client.message(StateFilter('reg_conditions'))
async def conditions(message: Message, state: FSMContext):
    cond = message.text
    if cond == 'Стандартные условия':
        data = await state.get_data()
        if data['who'] == 'zakazcik':
            await state.update_data(conditions='4.1. Обязанность Перевозчика  обеспечить перевозку конкретного груза наступает с момента согласования настоящего Договора-заявки Перевозчиком  и Заказчиком в письменной форме. Оформленный (заполненный) Перевозчиком Договор - Заявка должен быть согласован Заказчиком (подписан уполномоченным лицом и скреплен печатью Заказчика) в течение 30 (тридцати) минут с момента его получения. По истечении указанного срока, в случае если согласованный Заказчиком Договор-Заявка не направлен в адрес Перевозчика, Договор - Заявка считается согласованным. Договор - Заявка подписанный  сторонами путем обмена электронными и факсимильными сообщениями имеет юридическую силу.'
                                               ' 4.2. Заказчик  обязан организовать своими силами своевременные  погрузочно-разгрузочные работы на складах, базах и заводах, не допуская простоя автотранспорта под погрузкой/разгрузкой. Погрузка/разгрузка осуществляется по адресу,  указываемому в настоящем Договоре-Заявке.'
                                               ' 4.3. Заказчик гарантирует, что груз надлежащим образом упакован, затарен, запалечен и укреплен внутри кузова автотранспортного средства.'
                                               ' 4.4. Заказчик обеспечивает представителя Перевозчика  (водителя-экспедитора) полным пакетом документов, необходимых для перевозки груза (транспортная накладная в 4-экземплярах с указанием фактического адреса выгрузки).'
                                               ' 4.5. Перевозчик  вправе отказаться от приемки груза к перевозке, без каких-либо штрафных санкций со стороны Заказчика, если на груз отсутствует надлежащим образом оформленные сопроводительные документы (транспортная накладная/товарная накладная и т.п.); если груз имеет нарушения упаковки, помятости, подтеки, очевидные поломки, а также если данный груз не может быть перевезен на предоставленном транспортном средстве ввиду своих характеристик, о которых Перевозчик  не был уведомлен Заказчиком заранее в письменном виде.'
                                               ' 4.6. В случаях указанных в пункте 4.5. настоящего Договора-заявки, если Заказчик   настаивает на перевозке груза, упакованного, опломбированного и/или укрепленного в кузове транспортного средства ненадлежащим образом, либо имеющего нарушения упаковки, помятости, подтеки, очевидные поломки, несмотря на предупреждение перевозчика, Перевозчик вправе принять такой груз к перевозке. При этом в сопроводительных документах (транспортной накладной, товарной и т.п.) проставляется соответствующая отметка  и Перевозчик   не несет ответственность за недостатки груза, которые могут возникнуть в процессе  его перевозки вследствие  недостатков упаковки, пломбировки и/или крепления.'
                                               ' 4.7. В случае поступления груза Грузополучателю с расхождениями  по количеству и качеству,  Заказчик обязан составить (обеспечить составление Грузополучателем, не являющимся Заказчиком) в день обнаружения Акт. Акт составляется с обязательным участием уполномоченного представителя Перевозчика  и без подписи последнего недействителен.'
                                               ' 4.8. Простой  под погрузкой/разгрузкой более одного календарного дня, Заказчик обязан оплатить перевозчику  за одно транспортное средство  две тысячи рублей за каждые сутки простоя одного транспортного средства.'
                                               ' 4.9. Стоимость  услуг за предоставление дополнительного места погрузки/выгрузки составляет не менее двух тысяч рублей, конкретный размер оплаты согласовывается сторонами письменно.'
                                               ' 4.10. Претензии Заказчика к Перевозчику  в случае порчи, повреждения, утраты,  груза принимаются только при наличии подтверждающего ущерб, утрату, повреждение груза документа независимого экспертного учреждения. Заказчик обязан письменно уведомить представителя перевозчика  о проведении экспертизы.'
                                               ' 4.11. Ущерб  возмещается Перевозчиком на основании документально подтвержденных доказательств, прилагаемых к претензии.'
                                               ' 4.12. Перевозчик  вправе удерживать вверенные ему грузы в обеспечение причитающейся ему оплаты услуг по перевозке.'
                                               ' 4.13. За нарушение сроков оплаты перевозки Заказчик уплачивает Перевозчику  неустойку в размере 0,5% от цены перевозки установленной настоящим Договором-Заявкой.4.14. Любые исправления и изменения условий Договора-заявки действительны, если они совершены в письменном виде и подписаны уполномоченным представителем обеих сторон. Любые исправления, уточнения, изменения, сделанные «от руки» и внесенные в Договор-Заявку не имеют юридической силы.'
                                               ' 4.15. Иные условия, не предусмотренные настоящим Договором-Заявкой регламентируются  законодательством РФ.')
        else:
            await state.update_data(conditions='4.1. Обязанность Перевозчика  обеспечить перевозку конкретного груза наступает с момента согласования настоящего Договора-заявки Перевозчиком  и Заказчиком в письменной форме. Оформленный (заполненный) Перевозчиком Договор - Заявка должен быть согласован Заказчиком (подписан уполномоченным лицом и скреплен печатью Заказчика) в течение 30 (тридцати) минут с момента его получения. По истечении указанного срока, в случае если согласованный Заказчиком Договор-Заявка не направлен в адрес Перевозчика, Договор - Заявка считается согласованным. Договор - Заявка подписанный  сторонами путем обмена электронными и факсимильными сообщениями имеет юридическую силу. '
                                               '4.2. Заказчик  обязан организовать своими силами своевременные  погрузочно-разгрузочные работы на складах, базах и заводах, не допуская простоя автотранспорта под погрузкой/разгрузкой. Погрузка/разгрузка осуществляется по адресу,  указываемому в настоящем Договоре-Заявке.'
                                               ' 4.3. Заказчик гарантирует, что груз надлежащим образом упакован, затарен, запалечен и укреплен внутри кузова автотранспортного средства.'
                                               ' 4.4. Заказчик обеспечивает представителя Перевозчика  (водителя-экспедитора) полным пакетом документов, необходимых для перевозки груза (транспортная накладная в 4-экземплярах с указанием фактического адреса выгрузки).'
                                               ' 4.5. Перевозчик  вправе отказаться от приемки груза к перевозке, без каких-либо штрафных санкций со стороны Заказчика, если на груз отсутствует надлежащим образом оформленные сопроводительные документы (транспортная накладная/товарная накладная и т.п.); если груз имеет нарушения упаковки, помятости, подтеки, очевидные поломки, а также если данный груз не может быть перевезен на предоставленном транспортном средстве ввиду своих характеристик, о которых Перевозчик  не был уведомлен Заказчиком заранее в письменном виде.'
                                               ' 4.6. В случаях указанных в пункте 4.5. настоящего Договора-заявки, если Заказчик   настаивает на перевозке груза, упакованного, опломбированного и/или укрепленного в кузове транспортного средства ненадлежащим образом, либо имеющего нарушения упаковки, помятости, подтеки, очевидные поломки, несмотря на предупреждение перевозчика, Перевозчик вправе принять такой груз к перевозке. При этом в сопроводительных документах (транспортной накладной, товарной и т.п.) проставляется соответствующая отметка  и Перевозчик   не несет ответственность за недостатки груза, которые могут возникнуть в процессе  его перевозки вследствие  недостатков упаковки, пломбировки и/или крепления.'
                                               ' 4.7. В случае поступления груза Грузополучателю с расхождениями  по количеству и качеству,  Заказчик обязан составить (обеспечить составление Грузополучателем, не являющимся Заказчиком) в день обнаружения Акт. Акт составляется с обязательным участием уполномоченного представителя Перевозчика  и без подписи последнего недействителен.'
                                               ' 4.8. Простой  под погрузкой/разгрузкой более одного календарного дня, Заказчик обязан оплатить перевозчику  за одно транспортное средство  две тысячи рублей за каждые сутки простоя одного транспортного средства.'
                                               ' 4.9. Стоимость  услуг за предоставление дополнительного места погрузки/выгрузки составляет не менее двух тысяч рублей, конкретный размер оплаты согласовывается сторонами письменно.'
                                               ' 4.10. Претензии Заказчика к Перевозчику  в случае порчи, повреждения, утраты,  груза принимаются только при наличии подтверждающего ущерб, утрату, повреждение груза документа независимого экспертного учреждения. Заказчик обязан письменно уведомить представителя перевозчика  о проведении экспертизы.'
                                               ' 4.11. Ущерб  возмещается Перевозчиком на основании документально подтвержденных доказательств, прилагаемых к претензии.'
                                               ' 4.12. Перевозчик  вправе удерживать вверенные ему грузы в обеспечение причитающейся ему оплаты услуг по перевозке.'
                                               ' 4.13. За нарушение сроков оплаты перевозки Заказчик уплачивает Перевозчику  неустойку в размере 0,5% от цены перевозки установленной настоящим Договором-Заявкой.'
                                               ' 4.14. Любые исправления и изменения условий Договора-заявки действительны, если они совершены в письменном виде и подписаны уполномоченным представителем обеих сторон. Любые исправления, уточнения, изменения, сделанные «от руки» и внесенные в Договор-Заявку не имеют юридической силы.'
                                               ' 4.15. Иные условия, не предусмотренные настоящим Договором-Заявкой регламентируются  законодательством РФ.')
        print(data)
        data = await state.get_data()
        data_w = wrap_sentences_in_li(data, 'conditions')
        # Генерируем PDF
        pdf_bytes = generate_pdf(data)
        file = BufferedInputFile(pdf_bytes, filename="contract.pdf")
        await message.answer_document(file)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(base_dir, 'models')
        if data['logo_'] != ' ':
            file_to_delete = data['logo_']
            delete_path = os.path.join(save_dir, file_to_delete)
            try:
                os.remove(delete_path)
                print(f"Удален: {delete_path}")
            except Exception as e:
                print(f"Ошибка при удалении {delete_path}: {e}")
        elif data['stamp'] != ' ':
            file_to_delete = data['stamp']
            delete_path = os.path.join(save_dir, file_to_delete)
            os.remove(delete_path)
        elif data['fax'] != ' ':
            file_to_delete = data['fax']
            delete_path = os.path.join(save_dir, file_to_delete)
            os.remove(delete_path)
        else:
            pass
        await state.clear()
        await cmd_start(message, state)

    else:
        data = await state.get_data()
        old_text = data.get('conditions', '')
        new_text = old_text + message.text
        await state.update_data(conditions=new_text)
        #await message.answer(f"Получено {len(message.text)} символов, всего накоплено {len(new_text)} символов.")

        # Ждём 5 секунд, если за это время новых сообщений не будет, считаем ввод оконченным
        await asyncio.sleep(5)
        # Проверяем, не изменился ли текст за эти 5 секунд
        current_data = await state.get_data()
        if current_data.get('conditions') == new_text: # Ввод окончен

            print(current_data)
            data = wrap_sentences_in_li(current_data, 'conditions')
            # Генерируем PDF
            pdf_bytes = await asyncio.get_event_loop().run_in_executor(
                None, generate_pdf, current_data)
            file = BufferedInputFile(pdf_bytes, filename="contract.pdf")
            await message.answer_document(file)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            save_dir = os.path.join(base_dir, 'models')
            if current_data['logo_'] != ' ':
                file_to_delete = current_data['logo_']
                delete_path = os.path.join(save_dir, file_to_delete)
                try:
                    os.remove(delete_path)
                    print(f"Удален: {delete_path}")
                except Exception as e:
                    print(f"Ошибка при удалении {delete_path}: {e}")
            elif  current_data['stamp'] != ' ':
                file_to_delete = current_data['stamp']
                delete_path = os.path.join(save_dir, file_to_delete)
                os.remove(delete_path)
            elif current_data['fax'] != ' ':
                file_to_delete = current_data['fax']
                delete_path = os.path.join(save_dir, file_to_delete)
                os.remove(delete_path)
            else:
                pass


            await state.clear()
            await cmd_start(message, state)
