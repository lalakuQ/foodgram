from django.contrib.auth.models import AbstractUser
from django.db import models
from recipes.constants import (MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME,
                               MAX_LENGTH_LAST_NAME, MAX_LENGTH_USERNAME)


class User(AbstractUser):
    username = models.CharField(max_length=MAX_LENGTH_USERNAME, unique=True,
                                verbose_name='юзернейм')
    first_name = models.CharField(max_length=MAX_LENGTH_FIRST_NAME,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=MAX_LENGTH_LAST_NAME,
                                 verbose_name='Фамилия')
    email = models.EmailField(max_length=MAX_LENGTH_EMAIL, unique=True,
                              verbose_name='почта')
    avatar = models.ImageField(upload_to='users/', null=True,
                               verbose_name='аватарка')
    REQUIRED_FIELDS = ['first_name',
                       'last_name',
                       'email',
                       'avatar']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

        def __str__(self) -> str:
            return self.username
