from typing import ClassVar  # Importe isto

from sqlalchemy.orm import registry
from sqlmodel import SQLModel

# Criamos um registro único global
mapper_registry = registry()


# Criamos um SQLModel base que usa esse registro
# Annotamos o registry como ClassVar para que o Pydantic o ignore
class BaseModel(SQLModel):
    registry: ClassVar[registry] = mapper_registry

    class Config:
        # Garante que o Pydantic não tente validar o registry como dado
        ignored_types = (registry,)


# Agora gere a base com esse registro
BaseModel = mapper_registry.generate_base(cls=SQLModel)
