import base64
import io
import random
import string

from django.core.files.base import ContentFile
from rest_framework.generics import get_object_or_404
from django.http import HttpResponse
from recipes.constants import MAX_LENGTH_SHORTCODE
from recipes.models import Recipe, RecipeIngredient, RecipeTag, ShortUrl, UserRecipe

from rest_framework.response import Response
from rest_framework import status
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


def favorite_recipe_shopping_cart(request, pk, is_favorite=False,
                                  is_shopping_cart=False):
    from api.serializers import RecipeGetSerializer
    recipe = get_object_or_404(
        Recipe,
        pk=pk
    )
    try:
        user = request.user
        user_recipe, created = UserRecipe.objects.get_or_create(
            recipe=recipe,
            user=user,
        )
        if is_favorite:
            field = user_recipe.is_favorite
            attibute = 'is_favorite'
            err_no_obj = 'Рецепт не находится в ваших избранных'
            err_already_obj = 'Рецепт уже находится в избранных'
        else:
            field = user_recipe.is_in_shopping_cart
            attibute = 'is_in_shopping_cart'
            err_no_obj = 'Рецепт не находится в вашей корзине'
            err_already_obj = 'Рецепт уже находится в корзине'
        if request.method == 'DELETE':
            if field is True:
                setattr(user_recipe,
                        attibute,
                        False)
                user_recipe.save()
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )
            raise Exception(err_no_obj)
        if field is True:
            raise Exception(err_already_obj)
        setattr(user_recipe, attibute, True)
        user_recipe.save()
        obj = RecipeGetSerializer(recipe).data
        return Response(
            obj,
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response({
            'errors': str(e),
        }, status=status.HTTP_400_BAD_REQUEST)
