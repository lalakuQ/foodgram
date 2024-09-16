from django.urls import path, include
from rest_framework.authtoken import views
from rest_framework.routers import DefaultRouter
from djoser.views import TokenDestroyView
from .views import UserViewSet, RecipesViewSet, CustomTokenCreateView, TagViewSet, IngredientViewSet, URLRedirectView
router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path('auth/token/login/', CustomTokenCreateView.as_view(),
         name='token_login'),
    path('auth/token/logout/', TokenDestroyView.as_view(),
         name='token_logout'),
    path('users/me/avatar/', UserViewSet.as_view({'post': 'manage_avatar',
                                                 'delete': 'manage_avatar'})),
    path('users/', UserViewSet.as_view({'get': 'list'})),
    path('users/<int:pk>/subscribe', UserViewSet.as_view({
        'post': 'subscribtion',
        'delete': 'subscribtion'})),
    path('<slug:shortcode>/',
         URLRedirectView.as_view(),
         name='short_url_redirect'),
    path('', include('djoser.urls')),
    path('', include(router.urls)),
]
