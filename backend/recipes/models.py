from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = models.CharField()
    first_name = models.CharField()
    last_name = models.CharField()
    email = models.EmailField()
    avatar = models.ImageField()
    bookmarked_recipes = models.ManyToManyField('Recipe',
                                                related_name='users')
    shopping_recipes = models.ManyToManyField('Recipe')


class Follower(models.Model):
    user = models.ForeignKey(User,
                             related_name='following',)
    following_user = models.ForeignKey(User,
                                       related_name='followers')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following_user'],
                name='unique_followers'
            )
        ]


class Recipe(models.Model):
    author = models.ForeignKey('User',
                               related_name='recipes')
    name = models.CharField(unique=True)
    image = models.ImageField()
    description = models.TextField()
    ingredients = models.ManyToManyField(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    tag = models.ManyToManyField(
        'Tag',
        related_name='recipes',
    )
    prep_time = models.IntegerField()


class Tag(models.Model):
    name = models.CharField(unique=True)
    slug = models.SlugField(unique=True)


class Ingredient(models.Model):
    name = models.CharField(unique=True)
    unit = models.CharField()

