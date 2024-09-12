from django.contrib.auth.tokens import default_token_generator
from django.db.models import Avg
from django.forms import ValidationError
from django.db.models import Value, IntegerField
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from recipes.models import User, Follower, Ingredient, Recipe
from djoser.views import TokenCreateView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer
from .pagination import UserPagination
import base64

from django.core.files.base import ContentFile

class CustomTokenView(TokenCreateView):
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
    """ViewSet для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = UserPagination
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
        format, imgstr = avatar_data.split(';base64,')
        ext = format.split('/')[-1]
        file_name = f'avatar_{user.id}.{ext}'
        file_content = ContentFile(base64.b64decode(imgstr), name=file_name)
        user.avatar.save(file_name, file_content, save=True)
        avatar_url = request.build_absolute_uri(user.avatar.url)
        return Response({"avatar": avatar_url}, status=status.HTTP_200_OK)

'''class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с комментариями."""

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedAuthorAdminModerOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_review(self):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('reviews_id')
        return get_object_or_404(Review, id=review_id, title_id=title_id)

    def get_queryset(self):
        review = self.get_review()
        return review.comments.all()

    def perform_create(self, serializer):
        review = self.get_review()
        serializer.save(author=self.request.user, review=review)'''
