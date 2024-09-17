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
from recipes.models import User, Follower, Ingredient, Recipe, Tag, ShortUrl
from .filters import RecipeFilter
from djoser.views import TokenCreateView, TokenDestroyView
from urllib.parse import urlparse
from rest_framework.response import Response
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db import transaction


from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, TagSerializer, RecipeSerializer, IngredientSerializer, RecipeIngredientSerializer, RecipePostSerializer, FollowerSerializer, RecipeListSerializer
from .pagination import CustomPagination
from .permissions import IsAuthenticatedAuthorSuperuserOrReadOnly
import base64
from .utils import decode_img, shorten_url
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
                            status=status.HTTP_401_UNAUTHORIZED)
        return Response('Требуются пароль и почта',
                        status=status.HTTP_400_BAD_REQUEST)



class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    permission_classes = [AllowAny]

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
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
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribtion(self, request, pk):
        recipes_limit = request.query_params.get('recipes_limit', None)

        user = request.user
        following_user = get_object_or_404(
            User,
            pk=pk,
        )
        if request.method == 'DELETE':
            delete_sub = get_object_or_404(
                Follower,
                user=user,
                following_user=following_user
            )
            delete_sub.delete()
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
            return Response(serializer.data)
        return Response(
            {
                'Ошибка': 'Уже подписан или при подписке на себя самого'
            },
            status=status.HTTP_400_BAD_REQUEST)


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticatedAuthorSuperuserOrReadOnly,]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        url_path='favorite'
    )
    def bookmarked_recipe(self, request, pk):
        try:
            user = request.user
            recipe = get_object_or_404(
                Recipe,
                pk=pk
            )
            if request.method == 'DELETE':
                user.bookmarked_recipes.remove(recipe)
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )
            if user.bookmarked_recipes.filter(pk=pk).exists():
                raise Exception('Рецепт уже находится в избранных')
            user.bookmarked_recipes.add(recipe)
            obj = RecipeListSerializer(recipe).data
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
                                    secure=request.is_secure())
            return Response({
                'short-link': short_url
            }, status=status.HTTP_200_OK)

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
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class URLRedirectView(View):
    def get(self, request, shortcode=None, *args, **kwargs):
        try:
            instance = ShortUrl.objects.get(shortcode__iexact=shortcode)
            return HttpResponseRedirect(instance.url)
        except ShortUrl.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
