from django.contrib import admin
from .models import Follower, Ingredient, Recipe, Tag, User, RecipeIngredient, Unit


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'first_name',
        'last_name',
    )


@admin.register(Follower)
class FollowerAdmin(admin.ModelAdmin):
    list_display = (
        'user',
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'unit',
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
    )


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'author', 'prep_time')
    search_fields = ('name', 'author__username', 'author__email')
