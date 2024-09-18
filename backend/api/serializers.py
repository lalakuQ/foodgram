from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.validators import UnicodeUsernameValidator
from recipes.models import User, Follower, Ingredient, Recipe, Tag, Unit, RecipeIngredient, UserRecipe
from recipes.constants import MAX_LENGTH_USERNAME, MAX_LENGTH_EMAIL
from .utils import decode_img, create_recipe_ingredients


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
        create_recipe_ingredients(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)

        img_data = validated_data.get('image')
        if img_data:
            user = self.context['request'].user
            file_name, file_content = decode_img(img_data, user)
            instance.image.save(file_name, file_content, save=True)

        tags = validated_data.get('tags', [])
        instance.tags.set(tags)

        ingredients = validated_data.get('recipeingredient_set', [])
        instance.recipeingredient_set.all().delete()
        create_recipe_ingredients(instance, ingredients)

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation.update(
            {
                'id': instance.id,
                'tags': TagSerializer(instance.tags, many=True).data,
                'author': UserSerializer(instance.author).data,
                'is_favorite': False,
                'is_in_shopping_cart': False,
            }
        )
        representation['author'].pop('password')
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
