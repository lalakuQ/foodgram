from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError


def validate_username(value):
    """Проверяет корректность значения username."""

    # Проверка на недопустимое значение 'me'
    if value == 'me':
        raise ValidationError(
            f'Имя пользователя не может быть - {value}'
        )

    # Использование штатного валидатора UnicodeUsernameValidator
    validator = UnicodeUsernameValidator()
    validator(value)