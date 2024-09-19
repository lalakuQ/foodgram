from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from recipes.models import Ingredient, Recipe, Tag, Unit
from rest_framework.reverse import reverse

User = get_user_model()


class TestRecipeCreation(TestCase):
    TAG_1_NAME = 'Завтрак'
    TAG_1_SLUG = 'breakfast'

    TAG_2_NAME = 'Обед'
    TAG_2_SLUG = 'lunch'

    INGREDIENT_1_NAME = 'Капуста квашеная'
    INGREDIENT_1_MEASUREMENT_UNIT = 'кг'

    INGREDIENT_2_NAME = 'Масло'
    INGREDIENT_2_MEASUREMENT_UNIT = 'ч. ложка'

    RECIPE_1_INGREDIENT_1_ID = 1
    RECIPE_1_INGREDIENT_1_AMOUNT = 10
    RECIPE_1_INGREDIENT_2_ID = 2
    RECIPE_1_INGREDIENT_2_AMOUNT = 20
    RECIPE_1_TAG_1 = 1
    RECIPE_1_TAG_2 = 2
    RECIPE_1_IMAGE = ('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAA'
                      'AABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAA'
                      'ACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAg'
                      'gCByxOyYQAAAABJRU5ErkJggg==')
    RECIPE_1_NAME = 'Нечто съедобное (это не точно)'
    RECIPE_1_TEXT = 'Приготовьте как нибудь эти ингредиеты'
    RECIPE_1_COOKING_TIME = 5

    RECIPE_2_INGREDIENT_1_ID = 1
    RECIPE_2_INGREDIENT_1_AMOUNT = 10
    RECIPE_2_TAG_1 = 1
    RECIPE_2_IMAGE = ('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAA'
                      'AABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAA'
                      'ACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAg'
                      'gCByxOyYQAAAABJRU5ErkJggg==')
    RECIPE_2_NAME = 'Нечто съедобное (точно)'
    RECIPE_2_TEXT = 'Вероятно стоит это смешать.'
    RECIPE_2_COOKING_TIME = 5

    @classmethod
    def setUpTestData(cls):
        cls.author_1 = User.objects.create(username='Автор1',
                                           first_name='Имя1',
                                           last_name='Фамилия1',
                                           email='author1@gmail.com',)
        cls.author_1.set_password('author1')
        cls.author_1.save()
        cls.admin = User.objects.create(username='admin',
                                        first_name='admin',
                                        last_name='admin',
                                        email='admin@gmail.com',
                                        is_superuser=True)
        cls.admin.set_password('admin')
        cls.admin.save()
        cls.author_client_1 = Client()
        cls.url_login = reverse('api:token_login')

        data_author = {
            'email': 'author1@gmail.com',
            'password': 'author1'
        }
        response_author = cls.author_client_1.post(cls.url_login,
                                                   data=data_author,)
        token_author = response_author.data.get('auth_token')
        cls.author_headers = {
            'HTTP_AUTHORIZATION': f'Token {token_author}'}
        cls.admin_client = Client()

        data_admin = {
            'email': 'admin@gmail.com',
            'password': 'admin'
        }
        response_admin = cls.admin_client.post(cls.url_login,
                                               data_admin,
                                               format='json')
        token_admin = response_admin.data.get('auth_token')
        cls.admin_headers = {
            'HTTP_AUTHORIZATION': f'Token {token_admin}'}

        cls.recipe_url_create = reverse('api:recipes-list')
        cls.user_url_create = reverse('api:users-list')
        cls.ingredient_url_create = reverse('api:ingredients-list')
        cls.tag_url_create = reverse('api:tags-list')

        cls.form_data_tag_1 = {
            'name': cls.TAG_1_NAME,
            'slug': cls.TAG_1_SLUG
        }

        cls.form_data_tag_2 = {
            'name': cls.TAG_2_NAME,
            'slug': cls.TAG_2_SLUG
        }

        cls.form_data_recipe_1 = {
            'ingredients': [
                {
                    'id': cls.RECIPE_1_INGREDIENT_1_ID,
                    'amount': cls.RECIPE_1_INGREDIENT_1_AMOUNT
                },
                {
                    'id': cls.RECIPE_1_INGREDIENT_2_ID,
                    'amount': cls.RECIPE_1_INGREDIENT_2_AMOUNT
                }
            ],
            'tags': [
                cls.RECIPE_1_TAG_1,
                cls.RECIPE_1_TAG_2
            ],
            'image': cls.RECIPE_1_IMAGE,
            'name': cls.RECIPE_1_NAME,
            'text': cls.RECIPE_1_TEXT,
            'cooking_time': cls.RECIPE_1_COOKING_TIME
        }

        cls.form_data_recipe_2 = {
            'ingredients': [
                {
                    'id': cls.RECIPE_2_INGREDIENT_1_ID,
                    'amount': cls.RECIPE_2_INGREDIENT_1_AMOUNT
                },
            ],
            'tags': [
                cls.RECIPE_2_TAG_1
            ],
            'image': cls.RECIPE_2_IMAGE,
            'name': cls.RECIPE_2_NAME,
            'text': cls.RECIPE_2_TEXT,
            'cooking_time': cls.RECIPE_2_COOKING_TIME
        }
        cls.form_data_unit_1 = {
            'name': cls.INGREDIENT_1_MEASUREMENT_UNIT
        }
        cls.form_data_unit_2 = {
            'name': cls.INGREDIENT_2_MEASUREMENT_UNIT
        }

        units = [Unit(**cls.form_data_unit_1),
                 Unit(**cls.form_data_unit_2)]

        Unit.objects.bulk_create(units)

        cls.form_data_ingredient_1 = {
            'name': cls.INGREDIENT_1_NAME,
            'unit': Unit.objects.get(name=cls.INGREDIENT_1_MEASUREMENT_UNIT)
        }

        cls.form_data_ingredient_2 = {
            'name': cls.INGREDIENT_2_NAME,
            'unit': Unit.objects.get(name=cls.INGREDIENT_2_MEASUREMENT_UNIT)
        }
        tags = [Tag(**cls.form_data_tag_1), Tag(**cls.form_data_tag_2)]
        Tag.objects.bulk_create(tags)

        ingredients = [Ingredient(**cls.form_data_ingredient_1),
                       Ingredient(**cls.form_data_ingredient_2)]
        Ingredient.objects.bulk_create(ingredients)

    def test_user_can_create_recipe(self):
        recipe_count_inital = Recipe.objects.count()
        response = self.author_client_1.post(self.recipe_url_create,
                                             content_type='application/json',
                                             data=self.form_data_recipe_1,
                                             **self.author_headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        recipe_count_final = Recipe.objects.count()
        self.assertEqual(recipe_count_inital + 1, recipe_count_final)
        recipe = Recipe.objects.get()
        self.assertEqual(recipe.name, self.RECIPE_1_NAME)
        self.assertEqual(list(recipe.ingredients.all()),
                         list(Ingredient.objects.filter(
                             recipeingredient__recipe=recipe)))
        self.assertEqual(list(recipe.tags.all()),
                         list(Tag.objects.filter(
                             recipetag__recipe=recipe)))

    def test_admin_can_create_recipe(self):
        recipe_count_inital = Recipe.objects.count()
        response = self.admin_client.post(self.recipe_url_create,
                                          data=self.form_data_recipe_2,
                                          content_type='application/json',
                                          **self.admin_headers)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        recipe_count_final = Recipe.objects.count()
        self.assertEqual(recipe_count_inital + 1, recipe_count_final)
        recipe = Recipe.objects.get()
        self.assertEqual(recipe.name, self.RECIPE_2_NAME)
        self.assertEqual(list(recipe.ingredients.all()),
                         list(Ingredient.objects.filter(
                             recipeingredient__recipe=recipe)))
        self.assertEqual(list(recipe.tags.all()),
                         list(Tag.objects.filter(recipetag__recipe=recipe)))
