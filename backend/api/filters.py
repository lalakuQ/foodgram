import django_filters
from recipes.models import Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    is_favorited = django_filters.BooleanFilter(
        field_name='is_favorited',
        lookup_expr='exact'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='is_in_shopping_cart',
        lookup_expr='exact'
    )
    author = django_filters.CharFilter(
        field_name='author__id',
        lookup_expr='exact'
    )
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ['is_favorited',
                  'is_in_shopping_cart',
                  'author',
                  'tags']
