import re

def wrap_sentences_in_li(data: dict, key: str) -> dict:
    text = data.get(key, '')
    if not text:
        return data

    # Разбиваем текст на предложения с помощью регулярного выражения
    # Это простой вариант, который разбивает по точкам, восклицательным и вопросительным знакам
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZА-ЯЁ0-9])', text.strip())

    # Оборачиваем каждое предложение в <li>...</li>
    wrapped_sentences = [f"<li>{sentence.strip()}</li>" for sentence in sentences if sentence.strip()]

    # Собираем обратно в одну строку (например, без разделителей или с переносом строки)
    new_text = ''.join(wrapped_sentences)  # или '\n'.join(wrapped_sentences)

    # Обновляем словарь
    data[key] = new_text
    return data