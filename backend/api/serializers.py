from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.validators import UnicodeUsernameValidator
from recipes.models import User, Follower, Ingredient, Recipe, Tag
from recipes.constants import MAX_LENGTH_USERNAME, MAX_LENGTH_EMAIL


class UserSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        max_length=MAX_LENGTH_USERNAME,
        validators=[UnicodeUsernameValidator,
                    UniqueValidator(queryset=User.objects.all())],
    )

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        user_data = {
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'password': validated_data['password']
        }

        return user_data

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        request = self.context.get('request')

        if request and request.method == 'GET':
            if 'password' in representation:
                representation.pop('password')

        return representation

    class Meta:
        model = User
        fields = ['id',
                  'username',
                  'email',
                  'first_name',
                  'last_name',
                  'password']
