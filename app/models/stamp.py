import cv2
import numpy as np
import datetime
import os

def stamp_parsing(file):
    if not os.path.exists(file):
        print(f"Файл не найден: {file}")
        return
# Загружаем изображение
    img = cv2.imread(file)  # если есть альфа-канал
    if img is None:
        print(f"Не удалось загрузить изображение: {file}")
        return
    
# Если есть альфа-канал, можно оставить его или удалить
    if img.shape[2] == 4:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
    else:
        bgr = img
        alpha = None
    # Получаем размеры изображения
    height, width = bgr.shape[:2]
# Переводим в HSV
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

# Определяем диапазон синего цвета (подстроить под ваш оттенок)
    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([140, 255, 255])

# Создаем маску для синего
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Можно дополнительно очистить шумы (например, морфологией)
    kernel = np.ones((3,3), np.uint8)
    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

# Создаем новое изображение с прозрачным фоном
    # Создаем массив RGBA с прозрачным фоном по умолчанию
    result_rgba = np.zeros((height, width, 4), dtype=np.uint8)

    # Копируем цветные пиксели туда где маска активна
    result_rgba[:, :, :3] = bgr

    # Устанавливаем альфа-канал: 255 там где маска активна (объекты), 0 — прозрачность фона
    if alpha is not None:
        # Если исходное изображение имело альфа-канал,
        # можно оставить его или изменить по необходимости.
        pass

    result_rgba[:, :, 3] = 0  # по умолчанию делаем фон прозрачным

    # Устанавливаем непрозрачность там где маска активна
    result_rgba[mask_clean > 0, 3] = 255

    script_dir = os.path.dirname(os.path.abspath(__file__))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename_full_path = os.path.join(script_dir, f"processed_{timestamp}.png")

    # Сохраняем изображение с прозрачным фоном
    cv2.imwrite(output_filename_full_path, result_rgba)

    return os.path.basename(output_filename_full_path)