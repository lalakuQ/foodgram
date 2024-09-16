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
import hashlib
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from recipes.models import User, Follower, Ingredient, Recipe, Tag
from .filters import RecipeFilter
from djoser.views import TokenCreateView, TokenDestroyView
from urllib.parse import urlparse
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, TagSerializer, RecipeSerializer, IngredientSerializer, RecipeIngredientSerializer, RecipePostSerializer
from .pagination import CustomPagination
from .permissions import IsAuthenticatedAuthorSuperuserOrReadOnly
import base64
from .utils import decode_img
from django.core.files.base import ContentFile
from django_url_shortener.utils import shorten_url

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


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticatedAuthorSuperuserOrReadOnly,]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    @action(
        methods=['GET'],
        url_path='get-link',
        detail=True,
    )
    def get_short_link(self, request, pk):
        domain = request.get_host()
        path = request.path
        segments = path.strip('/').split('/')
        path = '/'.join(segments[:-1])
        created, short_url = shorten_url(f'{domain}/{path}')
        return Response({
            'short-link': short_url
        }, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return RecipePostSerializer
        return RecipeSerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(author=user, is_favorited=True)


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
