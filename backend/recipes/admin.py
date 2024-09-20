from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count, OuterRef, Subquery

from .models import (Follower, Ingredient, Recipe, RecipeIngredient, Tag, Unit,
                     UserRecipe)

admin.site.empty_value_display = 'Не задано'

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email'
    )
    list_editable = (
        'username',
        'first_name',
        'last_name',
        'email'
    )
    search_fields = (
        'email',
        'username'
    )
    list_display_links = None


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'following_user',
        'is_subscribed'
    )
    list_display_links = ('user', 'following_user')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'unit',
    )
    list_editable = list_display
    search_fields = (
        'name',
    )
    list_display_links = None


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display_links = None
    list_display = (
        'name',
        'slug',
    )
    list_editable = list_display


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    list_editable = list_display
    list_display_links = None


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'author', 'is_favorite_count')
    search_fields = ('name', 'author__username')
    list_filter = (
        'tags__name',
    )

    def is_favorite_count(self, obj):
        return obj.is_favorite_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            is_favorite_count=Count(Subquery(UserRecipe.objects.filter(
                recipe=OuterRef('id'), is_favorite=True).values('recipe'))
            )
        )
        return queryset
