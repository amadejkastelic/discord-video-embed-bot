import enum
import typing

from django.db import models


class StringEnumField(models.CharField):
    def __init__(
        self,
        enum: enum.Enum,  # pylint: disable=redefined-outer-name
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.enum = enum
        kwargs['max_length'] = kwargs.get('max_lenght') or max(len(e.value) for e in enum)
        kwargs['choices'] = [(e.value, e.name) for e in enum]
        super().__init__(*args, **kwargs)

    def from_db_value(self, value: str, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return self.enum(value) if value is not None else None

    def to_python(self, value: str) -> typing.Any:
        if isinstance(value, self.enum):
            return value

        return self.from_db_value(value=value)

    def get_prep_value(self, value: typing.Any) -> str:
        if isinstance(value, self.enum):
            return value.value

        return value

    def deconstruct(self) -> typing.Tuple[str, str, typing.Any, typing.Any]:
        name, path, args, kwargs = super().deconstruct()
        kwargs['enum'] = self.enum
        return name, path, args, kwargs


class IntEnumField(models.PositiveSmallIntegerField):
    def __init__(
        self,
        enum: enum.Enum,  # pylint: disable=redefined-outer-name
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.enum = enum
        kwargs['choices'] = [(e.value, e.name) for e in enum]
        super().__init__(*args, **kwargs)

    def from_db_value(self, value: str, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return self.enum(value) if value is not None else None

    def to_python(self, value: int) -> typing.Any:
        if isinstance(value, self.enum):
            return value

        return self.from_db_value(value=value)

    def get_prep_value(self, value: typing.Any) -> int:
        if isinstance(value, self.enum):
            return value.value

        return value

    def deconstruct(self) -> typing.Tuple[str, str, typing.Any, typing.Any]:
        name, path, args, kwargs = super().deconstruct()
        kwargs['enum'] = self.enum
        return name, path, args, kwargs
