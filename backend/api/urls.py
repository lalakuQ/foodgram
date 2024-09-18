from django.urls import include, path
from djoser.views import TokenDestroyView
from djoser.views import UserViewSet as djoser_UserViewSet
from rest_framework.routers import DefaultRouter

from .views import (CustomTokenCreateView, IngredientViewSet, RecipesViewSet,
                    TagViewSet, UserViewSet)

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
    path('users/set_password/', djoser_UserViewSet.as_view(
        {
            'post': 'set_password',
        }
    )),
    path('', include(router.urls)),
]
