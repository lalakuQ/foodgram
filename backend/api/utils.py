import base64
import io
import random
import string

from django.core.files.base import ContentFile
from django.http import HttpResponse
from recipes.constants import MAX_LENGTH_SHORTCODE
from recipes.models import RecipeIngredient, RecipeTag, ShortUrl


def decode_img(img_data, user):
    format, imgstr = img_data.split(';base64,')
    ext = format.split('/')[-1]
    file_name = f'img_{user.id}.{ext}'
    file_content = ContentFile(base64.b64decode(imgstr), name=file_name)
    return file_name, file_content


def create_recipe_ingredients(recipe, ingredients, tags):
    recipes_ingredients = [RecipeIngredient(
        ingredient=ingredient['id'],
        amount=ingredient['amount'],
        recipe=recipe) for ingredient in ingredients]
    recipes_tags = [RecipeTag(
        tag=tag,
        recipe=recipe) for tag in tags]
    try:
        RecipeIngredient.objects.bulk_create(
            recipes_ingredients
        )
        RecipeTag.objects.bulk_create(
            recipes_tags
        )
    except Exception:
        raise


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


def shorten_url(full_url, domain='localhost', secure=False):
    if secure is False:
        full_url = 'http://' + full_url
    else:
        full_url = 'https://' + full_url
    try:
        instance = ShortUrl.objects.get(
            url=full_url
        )
        return instance.get_short_url(domain)
    except ShortUrl.DoesNotExist:
        instance = None
    shortcode = create_shortcode()
    instance = ShortUrl.objects.create(
        url=full_url,
        shortcode=shortcode
    )
    return instance.get_short_url(domain)


def save_recipes_to_text_file(recipes):

    recipe_dict = {}
    for recipe in recipes:
        recipes_ingredients = RecipeIngredient.objects.filter(
            recipe=recipe
        )
        for recipe_ing in recipes_ingredients:
            ing = recipe_ing.ingredient
            if ing.name in recipe_dict.keys():
                recipe_dict[ing.name]['amount'] += recipe_ing.amount
            else:
                recipe_dict[ing.name] = {
                    'amount': recipe_ing.amount,
                    'unit': ing.unit.name
                }
    output = io.StringIO(newline='\n')
    output.write('Ингредиенты:' + '\n')
    for ing_name, data in recipe_dict.items():
        output.write(f"{ing_name}: {data['amount']} ({data['unit']})\n")

    output.seek(0)

    response = HttpResponse(output.read(), content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=recipes.txt'

    return response
