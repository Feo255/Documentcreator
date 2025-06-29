import requests

API_KEY = "DEMO9b559f4ac7622bb7656b2995480d105901af"  # Тестовый ключ
INN = "481400883724"  # ИНН компании


def get_company_info(inn: str) -> dict:
    url = f"https://focus-api.kontur.ru/api3/req?inn={inn}&key={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Обработка данных для юрлица или ИП
        print(data)
        print(len(inn))
        if len(inn) == 10:
            item = data[0]

            # Извлекаем ogrn
            ogrn = item.get('ogrn')

            # Извлекаем kpp из UL
            kpp = item.get('UL', {}).get('kpp')

            # Извлекаем full из legalName
            full_name = item.get('UL', {}).get('legalName', {}).get('full')

            # Извлекаем oneLineFormatOfAddressFias из parsedAddressRFFias внутри legalAddress
            # Проверим наличие этих ключей:
            address_info = None

            # Попытка взять из основного legalAddress:
            if isinstance(item.get('UL', {}).get('legalAddress', {}), dict):
                la = item['UL']['legalAddress']
                address_info = la.get('parsedAddressRFFias', {})
            elif isinstance(item.get('UL', {}).get('legalAddress', {}), list):
                # если список, взять первый элемент (если есть)
                la_list = item['UL']['legalAddress']
                if len(la_list) > 0:
                    address_info = la_list[0].get('parsedAddressRFFias', {})

            oneLineFormatOfAddressFias = address_info.get('oneLineFormatOfAddressFias') if address_info else None

            # Из heads берем fio и position (предположим, что интересует первый элемент)
            item2 = item.get('UL', {}).get('heads')
            item3 = item2[0]
            fio = item3.get('fio')
            position = item3.get('position')

            # Итоговый словарь
            result = {
                'ogrn': ogrn,
                'kpp': kpp,
                'full': full_name,
                'oneLineFormatOfAddressFias': oneLineFormatOfAddressFias,
                'fio': fio,
                'position': position,
            }

            print(result)

            return result
        else:
            item = data[0]
            ogrn = item.get('ogrn')
            fio = item.get('IP', {}).get('fio')

            result = {
                'ogrn': ogrn,
                'kpp': ' ',
                'full': fio,
                'oneLineFormatOfAddressFias': ' ',
                'fio': fio,
                'position': ' ',
            }
            return result

    except requests.exceptions.HTTPError as e:
        print(f"Ошибка запроса: {e}")
    except Exception as e:
        print(f"Ошибка: {e}")

result = get_company_info(INN)
print(result)