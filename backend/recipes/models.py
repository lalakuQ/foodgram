from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse

from .constants import (MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME,
                        MAX_LENGTH_LAST_NAME, MAX_LENGTH_NAME,
                        MAX_LENGTH_SHORTCODE, MAX_LENGTH_SLUG,
                        MAX_LENGTH_USERNAME)


class User(AbstractUser):
    username = models.CharField(max_length=MAX_LENGTH_USERNAME, unique=True,)
    first_name = models.CharField(max_length=MAX_LENGTH_FIRST_NAME)
    last_name = models.CharField(max_length=MAX_LENGTH_LAST_NAME)
    email = models.EmailField(max_length=MAX_LENGTH_EMAIL, unique=True)
    avatar = models.ImageField(upload_to='users/', null=True)
    REQUIRED_FIELDS = ['first_name',
                       'last_name',
                       'email',
                       'avatar']

    def __str__(self) -> str:
        return self.username


class UserRecipe(models.Model):
    is_in_shopping_cart = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE
    )


class Follower(models.Model):
    user = models.ForeignKey(User,
                             related_name='following',
                             on_delete=models.CASCADE)
    following_user = models.ForeignKey(User,
                                       related_name='followers',
                                       on_delete=models.CASCADE)
    is_subscribed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following_user'],
                name='unique_followers'
            )
        ]


class TagIngredientUnit(models.Model):
    name = models.CharField(unique=True, max_length=MAX_LENGTH_NAME)

    def __str__(self) -> str:
        return self.name

    class Meta:
        abstract = True


class Tag(TagIngredientUnit):
    slug = models.SlugField(unique=True, max_length=MAX_LENGTH_SLUG)


class Ingredient(TagIngredientUnit):
    unit = models.ForeignKey('Unit', null=True, on_delete=models.SET_NULL)


class Unit(TagIngredientUnit):
    pass


class Recipe(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE)
    name = models.CharField(unique=True, max_length=MAX_LENGTH_NAME)
    image = models.ImageField(upload_to='recipes/')
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField()

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ['-created_at']


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'],
                name='unique_recipe_tag'
            )
        ]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class ShortUrl(models.Model):
    url = models.CharField(max_length=256)
    shortcode = models.CharField(max_length=MAX_LENGTH_SHORTCODE)

    def get_short_url(self, domain):
        url_path = domain + reverse('short_url_redirect',
                                    kwargs={'shortcode': self.shortcode})
        return url_path
