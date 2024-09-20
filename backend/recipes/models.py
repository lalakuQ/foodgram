from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

from .constants import (MAX_LENGTH_NAME, MAX_LENGTH_SHORTCODE,
                        MAX_LENGTH_SLUG)

User = get_user_model()


class UserRecipe(models.Model):
    is_in_shopping_cart = models.BooleanField(default=False,
                                              verbose_name='в корзине')
    is_favorite = models.BooleanField(default=False,
                                      verbose_name='избранное')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        verbose_name='рецепт'
    )


class Follower(models.Model):
    user = models.ForeignKey(User,
                             related_name='following',
                             on_delete=models.CASCADE,
                             verbose_name='фолловер')
    following_user = models.ForeignKey(User,
                                       related_name='followers',
                                       on_delete=models.CASCADE,
                                       verbose_name='пользователь')
    is_subscribed = models.BooleanField(default=False,
                                        verbose_name='подписка')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following_user'],
                name='unique_followers'
            )
        ]
        verbose_name = 'фолловер'
        verbose_name_plural = 'Фолловеры'


class TagIngredientUnit(models.Model):
    name = models.CharField(unique=True, max_length=MAX_LENGTH_NAME,
                            verbose_name='наименование')

    def __str__(self) -> str:
        return self.name

    class Meta:
        abstract = True


class Tag(TagIngredientUnit):
    slug = models.SlugField(unique=True, max_length=MAX_LENGTH_SLUG,
                            verbose_name='идентификатор')

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Ingredient(TagIngredientUnit):
    unit = models.ForeignKey('Unit', null=True, on_delete=models.SET_NULL,
                             verbose_name='единица измерения')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Unit(TagIngredientUnit):
    pass

    class Meta:
        verbose_name = 'едининца измерения'
        verbose_name_plural = 'Единицы измерения'


class Recipe(models.Model):
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='создано')
    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE,
                               verbose_name='создано')
    name = models.CharField(unique=True, max_length=MAX_LENGTH_NAME,
                            verbose_name='имя')
    image = models.ImageField(upload_to='recipes/',
                              verbose_name='картинка')
    text = models.TextField(verbose_name='описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
        verbose_name='теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='время приготовления'
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='рецепт')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE,
                            verbose_name='тег')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'],
                name='unique_recipe_tag'
            )
        ]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='рецепт')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   verbose_name='ингредиент')
    amount = models.PositiveSmallIntegerField(
        verbose_name='количество'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class ShortUrl(models.Model):
    url = models.CharField(max_length=256,
                           verbose_name='ссылка')
    shortcode = models.CharField(max_length=MAX_LENGTH_SHORTCODE,
                                 verbose_name='уникальный код')

    def get_short_url(self, domain):
        url_path = domain + reverse('short_url_redirect',
                                    kwargs={'shortcode': self.shortcode})
        return url_path

    class Meta:
        verbose_name = 'короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
