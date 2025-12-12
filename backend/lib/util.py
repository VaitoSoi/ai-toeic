from typing import Optional, Type, TypeVar, cast

from sqlmodel import JSON, SQLModel, TypeDecorator

T = TypeVar('T', bound=SQLModel)

class PydanticJSON(TypeDecorator):
    impl = JSON

    def __init__(self, pydantic_model: Type[T]):
        super().__init__()
        self.pydantic_model = pydantic_model

    def process_bind_param(self, value: Optional[T], dialect) -> Optional[dict]:
        # Python -> Database (Saving)
        if value is None:
            return None
        # Use mode='json' to handle nested types like datetime automatically
        return value.model_dump(mode='json')

    def process_result_value(self, value: Optional[dict], dialect) -> Optional[T]:
        # Database -> Python (Loading)
        if value is None:
            return None
        return cast(T, self.pydantic_model.model_validate(value))
    
class PydanticListJSON(TypeDecorator):
    impl = JSON

    def __init__(self, pydantic_model: Type[T]):
        super().__init__()
        self.pydantic_model = pydantic_model

    def process_bind_param(self, value: Optional[list[T]], dialect) -> Optional[list[dict]]:
        if value is None:
            return None
        
        if not isinstance(value, list):
            raise TypeError(f"Expected list but got {type(value)}: {value}. PydanticListJSON can only handle lists of SQLModel objects.")
        
        result = []
        for i, item in enumerate(value):
            if hasattr(item, 'model_dump'):
                result.append(item.model_dump(mode='json'))
            elif isinstance(item, dict):
                result.append(item)
            else:
                raise TypeError(f"Cannot serialize item {i} of type {type(item)}: {item}. Expected SQLModel with model_dump method.")
        return result

    def process_result_value(self, value: Optional[list[dict]], dialect) -> Optional[list[T]]:
        if value is None:
            return None
        return cast(list[T], [self.pydantic_model.model_validate(item) for item in value])
