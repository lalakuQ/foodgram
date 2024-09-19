import django_filters
from recipes.models import Ingredient, Recipe, Tag, UserRecipe


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.NumberFilter(method='filter_is_favorite')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart'
    )
    author = django_filters.CharFilter(
        field_name='author__id',
        lookup_expr='exact'
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )

    def filter_user_recipe(self, queryset, value, field, name=None):
        user = self.request.user
        if not user.is_authenticated:
            return queryset
        for recipe in queryset:
            UserRecipe.objects.get_or_create(
                recipe=recipe,
                user=user
            )
        if value == 0 or value == 1:
            filter_kwargs = {
                'userrecipe__user': user,
                f'userrecipe__{field}': bool(value)
            }
            return queryset.filter(**filter_kwargs)
        return queryset

    def filter_is_favorite(self, queryset, name, value):
        return self.filter_user_recipe(queryset,
                                       value,
                                       field='is_favorite')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self.filter_user_recipe(queryset,
                                       value,
                                       field='is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['is_favorited',
                  'is_in_shopping_cart',
                  'author',
                  'tags',]


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='startswith'
    )

    class Meta:
        model = Ingredient
        fields = [
            'name',
        ]
