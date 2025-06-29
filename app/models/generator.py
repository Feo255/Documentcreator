import os
from aiogram.types import BufferedInputFile

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def generate_pdf(data: dict):
    # Создаём окружение Jinja2, указывая папку с шаблонами
   # template_dir = r'C:\Users\synesis1\PycharmProjects\BotLogist\.venv\app\models'
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, '.') 
    env = Environment(loader=FileSystemLoader(template_dir))
    if data['who'] == 'trans':
        template = env.get_template('template2.html')

        # Рендерим HTML, подставляя данные
        html_content = template.render(**data)

        # Генерируем PDF из HTML
        pdf_bytes = HTML(string=html_content, base_url=template_dir).write_pdf()

        return pdf_bytes
    else:
        template = env.get_template('template1.html')

    # Рендерим HTML, подставляя данные
        html_content = template.render(**data)

    # Генерируем PDF из HTML
        pdf_bytes = HTML(string=html_content, base_url=template_dir).write_pdf()

        return pdf_bytes