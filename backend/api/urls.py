from django.urls import path, include
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomTokenView
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/token/login/', CustomTokenView.as_view(), name='token_login'),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/avatar/', UserViewSet.as_view({'post': 'manage_avatar',
                                                 'delete': 'manage_avatar'})),
    path('users/', UserViewSet.as_view({'get': 'list'})),
    path('', include('djoser.urls')),
    path('', include(router.urls)),
]
