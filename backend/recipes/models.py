from .constants import (MAX_LENGTH_EMAIL,
                        MAX_LENGTH_FIRST_NAME,
                        MAX_LENGTH_LAST_NAME,
                        MAX_LENGTH_NAME,
                        MAX_LENGTH_ROLE,
                        MAX_LENGTH_SLUG,
                        MAX_LENGTH_USERNAME,
                        MIN_VALUE_COOKING_TIME)
from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework import validators
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    username = models.CharField(max_length=MAX_LENGTH_USERNAME,
                                unique=True)
    first_name = models.CharField(max_length=MAX_LENGTH_FIRST_NAME)
    last_name = models.CharField(max_length=MAX_LENGTH_LAST_NAME)
    email = models.EmailField(max_length=MAX_LENGTH_EMAIL, unique=True)
    avatar = models.ImageField(upload_to='users/')
    is_subscribed = models.BooleanField(default=False)
    bookmarked_recipes = models.ManyToManyField('Recipe', related_name='users')
    shopping_recipes = models.ManyToManyField('Recipe',)
    REQUIRED_FIELDS = ['first_name',
                       'last_name',
                       'email',
                       'is_subscribed',
                       'avatar']


class Follower(models.Model):
    user = models.ForeignKey(User,
                             related_name='following',
                             on_delete=models.CASCADE)
    following_user = models.ForeignKey(User,
                                       related_name='followers',
                                       on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following_user'],
                name='unique_followers'
            )
        ]


class Tag(models.Model):
    name = models.CharField(unique=True, max_length=MAX_LENGTH_NAME)
    slug = models.SlugField(unique=True, max_length=MAX_LENGTH_SLUG)


class Ingredient(models.Model):
    name = models.CharField(unique=True, max_length=MAX_LENGTH_NAME)
    unit = models.ForeignKey('Unit', null=True, on_delete=models.SET_NULL)


class Unit(models.Model):
    name = models.CharField(unique=True, max_length=MAX_LENGTH_NAME)


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE)
    name = models.CharField(unique=True, max_length=MAX_LENGTH_NAME)
    image = models.ImageField()
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_VALUE_COOKING_TIME)]
    )
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=5, decimal_places=2)