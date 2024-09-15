from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.validators import UnicodeUsernameValidator
from recipes.models import User, Follower, Ingredient, Recipe, Tag, Unit, RecipeIngredient
from recipes.constants import MAX_LENGTH_USERNAME, MAX_LENGTH_EMAIL
from .utils import decode_img

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
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password',
            'avatar']


class IngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.CharField(source='unit.name')

    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'measurement_unit'
        ]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'amount'
        ]

    def to_representation(self, instance):
        return {
            'id': instance.ingredient.id,
            'name': instance.ingredient.name,
            'measurement_unit': instance.ingredient.unit.name,
            'amount': str(instance.amount)
        }


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipeingredient_set')
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = serializers.CharField()

    def create(self, validated_data):
        user = self.context['request'].user
        img_data = validated_data.pop('image')
        ingredients = validated_data.pop('recipeingredient_set')
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        file_name, file_content = decode_img(img_data, user)
        recipe.image.save(file_name, file_content, save=True)
        recipe.tags.add(*tags)
        recipes_ingredients = [RecipeIngredient(
            ingredient=ingredient['id'],
            amount=ingredient['amount'],
            recipe=recipe) for ingredient in ingredients]
        RecipeIngredient.objects.bulk_create(
            recipes_ingredients
        )

        return recipe

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(instance.tags, many=True).data
        return representation

    class Meta:
        model = Recipe
        fields = [
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        ]

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(source='recipeingredient_set',
                                             many=True)
    tags = TagSerializer(many=True)
    author = UserSerializer()

    class Meta:
        model = Recipe
        fields = '__all__'
