from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg
from django.forms import ValidationError
from django.db.models import Value, IntegerField
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from djoser import utils
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.views import View
import hashlib
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from recipes.models import User, Follower, Ingredient, Recipe, Tag, ShortUrl, UserRecipe
from .filters import RecipeFilter, IngredientFilter
from djoser.views import TokenCreateView, TokenDestroyView
from urllib.parse import urlparse
from rest_framework.response import Response
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db import transaction


from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, TagSerializer, RecipeSerializer, IngredientSerializer, RecipeIngredientSerializer, RecipePostSerializer, FollowerSerializer, RecipeGetSerializer
from .pagination import CustomPagination
from .permissions import IsAuthenticatedAuthorSuperuserOrReadOnly
import base64
from .utils import decode_img, shorten_url, save_recipes_to_text_file
from django.core.files.base import ContentFile


class CustomTokenCreateView(TokenCreateView,):

    def post(self, request, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if email and password:
            user = authenticate(request, email=email, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)

                return Response({'auth_token': str(token)},
                                status=status.HTTP_200_OK)
            return Response('Неверные данные',
                            status=status.HTTP_400_BAD_REQUEST)
        return Response('Требуются пароль и почта',
                        status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(
        methods=['POST', 'DELETE', 'PUT'],
        detail=False,
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def manage_avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete()
            return Response('Аватар успешно удален',
                            status=status.HTTP_204_NO_CONTENT)
        avatar_data = request.data.get('avatar')
        if not avatar_data:
            return Response({'avatar': 'Обязательное поле.'},
                            status=status.HTTP_400_BAD_REQUEST)
        file_name, file_content = decode_img(img_data=avatar_data,
                                             user=user)
        user.avatar.save(file_name, file_content, save=True)
        avatar_url = request.build_absolute_uri(user.avatar.url)
        return Response({"avatar": avatar_url}, status=status.HTTP_200_OK)

    @action(
        methods=['GET'],
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        user = UserSerializer(request.user, context={
            'request': request
        }).data
        return Response(user, status=status.HTTP_200_OK)

    @action(
        methods=['GET'],
        detail=False,
        url_path='subscriptions',
    )
    def get_subscriptions(self, request):
        recipes_limit = request.query_params.get('recipes_limit', None)
        queryset = request.user.following.all()
        page = self.paginate_queryset(queryset)
        serializer = FollowerSerializer(
            page,
            many=True,
            context={'recipes_limit': recipes_limit},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        url_path='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscription(self, request, pk):
        recipes_limit = request.query_params.get('recipes_limit', None)

        user = request.user
        following_user = get_object_or_404(
            User,
            pk=pk,
        )
        if request.method == 'DELETE':
            try:
                delete_sub = Follower.objects.get(
                    user=user,
                    following_user=following_user
                )
                delete_sub.delete()
            except Exception:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )

        instance = Follower.objects.filter(
            user=user,
            following_user=following_user
        ).exists()
        if user != following_user and not instance:
            object = Follower.objects.create(
                user=user,
                following_user=following_user,
                is_subscribed=True
            )

            serializer = FollowerSerializer(
                object,
                context={'recipes_limit': recipes_limit}
            )
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        return Response(
            {
                'Ошибка': 'Уже подписан или при подписке на себя самого'
            },
            status=status.HTTP_400_BAD_REQUEST)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticatedAuthorSuperuserOrReadOnly,]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        url_path='favorite'
    )
    def favorite_recipe(self, request, pk):
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
            is_favorite = user_recipe.is_favorite
            if request.method == 'DELETE':
                if is_favorite is True:
                    user_recipe.is_favorite = False
                    user_recipe.save()
                    return Response(
                        status=status.HTTP_204_NO_CONTENT
                    )
                raise Exception('Рецепт не находится в ваших избранных')
            if is_favorite is True:
                raise Exception('Рецепт уже находится в избранных')
            user_recipe.is_favorite = True
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

    @action(
        methods=['GET'],
        url_path='get-link',
        detail=True,
    )
    def get_short_link(self, request, pk):
        try:
            get_object_or_404(
                Recipe,
                pk=pk
            )
            domain = request.get_host()
            path = request.path
            segments = path.strip('/').split('/')
            path = '/'.join(segments[:-1])
            short_url = shorten_url(f'{domain}/{path}',
                                    domain,
                                    secure=request.is_secure())
            return Response({
                'short-link': short_url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'errors': str(e),
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['GET'],
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def get_shopping_cart_file(self, request):
        return save_recipes_to_text_file(
            Recipe.objects.filter(
                userrecipe__user=request.user,
                userrecipe__is_in_shopping_cart=True,
            )
        )

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        url_path='shopping_cart',
    )
    def recipe_shopping_cart(self, request, pk):
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
            is_in_shopping_cart = user_recipe.is_in_shopping_cart
            if request.method == 'DELETE':
                if is_in_shopping_cart is True:
                    user_recipe.is_in_shopping_cart = False
                    user_recipe.save()
                    return Response(
                        status=status.HTTP_204_NO_CONTENT
                    )
                raise Exception('Рецепт не находится в вашей корзине')
            if is_in_shopping_cart is True:
                raise Exception('Рецепт уже находится в корзине')
            user_recipe.is_in_shopping_cart = True
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

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return RecipePostSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(author=user)


class TagViewSet(viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.GenericViewSet,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,):
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class URLRedirectView(View):
    def get(self, request, shortcode=None, *args, **kwargs):
        try:
            instance = ShortUrl.objects.get(shortcode__iexact=shortcode)
            return HttpResponseRedirect(instance.url)
        except ShortUrl.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
