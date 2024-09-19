import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import (Ingredient, Unit)


DIR_PATH = os.path.join(settings.BASE_DIR, 'data')
FILES_PATH = {
    'ingredients': (os.path.join(DIR_PATH, 'ingredients.csv'), Ingredient),
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--files', type=str,
                            help=('Список названий файлов (без расширения)'
                                  'если не указано - импорт всех файлов.'),
                            nargs='*',
                            required=False)

    def handle(self, *args, **options):
        try:
            with open(FILES_PATH['ingredients'][0], newline='',
                      encoding='utf-8') as file:
                dict_reader = csv.DictReader(file)
                instances = []
                for row in dict_reader:
                    row['unit'], created = Unit.objects.get_or_create(
                        name=row['unit']
                    )
                    instance = Ingredient(**row)
                    instances.append(instance)

                Ingredient.objects.bulk_create(instances)

            self.stdout.write(self.style.SUCCESS(
                'Данные успешно импортированы из: ingredients.csv'))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f'Не найден файл: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR((f'Ошибка: {e}')))
