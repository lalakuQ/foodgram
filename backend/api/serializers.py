from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator
from recipes.constants import (MAX_LENGTH_EMAIL,
                               MAX_LENGTH_USERNAME,
                               MIN_VALUE_COOKING_TIME)
from recipes.models import (Follower, Ingredient, Recipe, RecipeIngredient,
                            Tag, User, UserRecipe)
from rest_framework import serializers
from rest_framework.validators import (UniqueValidator, ValidationError)

from .utils import create_recipe_ingredients, decode_img


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        validators=[UnicodeUsernameValidator(),
                    UniqueValidator(queryset=User.objects.all())],
    )
    username = serializers.CharField(
        max_length=MAX_LENGTH_USERNAME,
        validators=[UnicodeUsernameValidator(),
                    UniqueValidator(queryset=User.objects.all())],
    )

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        user_data = {
            'id': user.id,
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
        representation.pop('password', None)
        if request and not request.method == 'GET':
            representation.pop('avatar', None)
            return representation
        try:
            following = Follower.objects.get(
                user=request.user,
                following_user=instance
            )
            following_dict = {
                'is_subscribed': following.is_subscribed
            }
        except Exception:
            following_dict = {
                'is_subscribed': False
            }
        representation.update(following_dict)
        return representation

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
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
    amount = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(MIN_VALUE_COOKING_TIME)])

    class Meta:
        model = RecipeIngredient
        fields = [
            'id',
            'amount',
        ]

    def to_representation(self, instance):
        return {
            'id': instance.ingredient.id,
            'name': instance.ingredient.name,
            'measurement_unit': instance.ingredient.unit.name,
            'amount': instance.amount
        }


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True,
                                             source='recipeingredient_set',
                                             allow_empty=False,
                                             )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        allow_empty=False
    )
    image = serializers.CharField()
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(1)]
    )

    def create(self, validated_data):
        user = self.context['request'].user
        img_data = validated_data.pop('image')
        ingredients = validated_data.pop('recipeingredient_set')
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        file_name, file_content = decode_img(img_data, user)
        recipe.image.save(file_name, file_content, save=True)
        try:
            create_recipe_ingredients(recipe, ingredients, tags)
        except Exception as e:
            raise ValidationError(str(e))

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)

        img_data = validated_data.get('image', None)
        if img_data:
            user = self.context['request'].user
            file_name, file_content = decode_img(img_data, user)
            instance.image.save(file_name, file_content, save=True)

        tags = validated_data.get('tags', [])
        ingredients = validated_data.get('recipeingredient_set', [])
        if len(tags) == 0 or len(ingredients) == 0:
            raise ValidationError('Теги и ингредиенты не могут быть пустыми')
        instance.recipeingredient_set.all().delete()
        instance.recipetag_set.all().delete()
        try:
            create_recipe_ingredients(instance, ingredients, tags)
        except Exception as e:
            raise ValidationError(str(e))

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation.update(
            {
                'id': instance.id,
                'tags': TagSerializer(instance.tags, many=True).data,
                'author': UserSerializer(instance.author).data,
                'is_favorited': False,
                'is_in_shopping_cart': False,
            }
        )
        return representation

    class Meta:
        model = Recipe
        fields = [
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        ]


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(source='recipeingredient_set',
                                             many=True)
    tags = TagSerializer(many=True)
    author = UserSerializer()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        recipe_dict = {}
        request = self.context.get('request')
        try:
            user_recipe = UserRecipe.objects.get(recipe=instance,
                                                 user=request.user)
            recipe_dict = {
                'is_favorited': user_recipe.is_favorite,
                'is_in_shopping_cart': user_recipe.is_in_shopping_cart,
            }
        except Exception:
            recipe_dict = {
                'is_favorited': False,
                'is_in_shopping_cart': False,
            }
        representation.update(recipe_dict)
        return representation

    class Meta:
        model = Recipe
        fields = '__all__'


class RecipeGetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class FollowedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar'
        ]


class FollowerSerializer(serializers.ModelSerializer):

    following_user = FollowedUserSerializer()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        recipes_limit = self.context.get('recipes_limit')
        following_user_dict = representation.pop('following_user')

        representation.update(dict(following_user_dict))

        following_user = instance.following_user
        recipes = following_user.recipes.all()
        recipes_count = recipes.count()
        representation['recipes_count'] = recipes_count
        if recipes_limit and recipes_count != 0:
            try:
                recipes = recipes[:int(recipes_limit)]
                representation['recipes'] = RecipeGetSerializer(
                    recipes,
                    many=True).data
                return representation
            except ValueError as e:
                return e
        representation['recipes'] = []
        return representation

    class Meta:
        model = Follower
        fields = [
            'following_user',
            'is_subscribed'
        ]
