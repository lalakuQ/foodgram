from django.urls import path, include
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CustomTokenView
router = DefaultRouter()
router.register('users', UserViewSet, basename='users')


urlpatterns = [
    path('auth/token/login/', CustomTokenView.as_view()),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]
