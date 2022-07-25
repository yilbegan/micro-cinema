from typing import Any
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

import dataclass_factory
from tortoise import fields
from tortoise import Model
from tortoise.exceptions import FieldError

T = TypeVar("T")


class DataClassField(fields.JSONField):
    def __init__(
        self,
        type_: Type[T],
        default: Optional[T] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(default=default, **kwargs)
        self.type: Type[T] = type_
        self.factory = dataclass_factory.Factory()

    def to_db_value(
        self, value: T, instance: Union[Type[Model], Model]
    ) -> Optional[str]:
        return self.encoder(self.factory.dump(value))

    def to_python_value(self, value: Optional[Union[str, dict, list]]) -> Optional[T]:
        if isinstance(value, str):
            try:
                value = self.decoder(value)
            except Exception:
                raise FieldError(f"Value {value} is invalid json value.")
        if value is None:
            return None
        return self.factory.load(value, self.type)
