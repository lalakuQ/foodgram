import base64
import random
import string
from django.core.files.base import ContentFile
from recipes.models import RecipeIngredient, ShortUrl
from recipes.constants import MAX_LENGTH_SHORTCODE

def decode_img(img_data, user):
    format, imgstr = img_data.split(';base64,')
    ext = format.split('/')[-1]
    file_name = f'img_{user.id}.{ext}'
    file_content = ContentFile(base64.b64decode(imgstr), name=file_name)
    return file_name, file_content


def create_recipe_ingredients(recipe, ingredients):
    recipes_ingredients = [RecipeIngredient(
        ingredient=ingredient['id'],
        amount=ingredient['amount'],
        recipe=recipe) for ingredient in ingredients]
    RecipeIngredient.objects.bulk_create(
        recipes_ingredients
    )


def code_generator(
        size=MAX_LENGTH_SHORTCODE,
        chars=string.ascii_lowercase + string.digits + string.ascii_uppercase):
    return ''.join(random.choice(chars) for _ in range(size))


def create_shortcode(size=MAX_LENGTH_SHORTCODE):
    code = code_generator(size=size)
    obj = ShortUrl.objects.filter(shortcode=code).exists()
    if obj:
        return create_shortcode(size=size)
    return code


def shorten_url(full_url, secure=False):
    if secure is False:
        full_url = 'http://' + full_url
    else:
        full_url = 'https://' + full_url
    try:
        instance = ShortUrl.objects.get(
            url=full_url
        )
    except ShortUrl.DoesNotExist:
        instance = None
    if instance:
        return instance.get_short_url()
    shortcode = create_shortcode()
    instance = ShortUrl.objects.create(
        url=full_url,
        shortcode=shortcode
    )
    return instance.get_short_url()