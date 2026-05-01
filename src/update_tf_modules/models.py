from typing import Literal, Annotated

from pydantic import BaseModel, Field, TypeAdapter

class BaseModule(BaseModel):
    name: str
    glob: str | None = None
    file: str | None = None
    files: list[str] | None = None

class GitHubModule(BaseModule):
    type: Literal["github"]
    repo: str
    source_prefix: str
    lookup: Literal["release", "tag"] = "release"
    pin: Literal["sha", "tag"] = "sha"

class RegistryModule(BaseModule):
    type: Literal["registry"]
    source: str

Module = Annotated[GitHubModule | RegistryModule, Field(discriminator="type")]

_adapter = TypeAdapter(Module) # type: ignore

def validate_manifest_modules(modules: list[dict[str, object]]) -> list[Module]:
    return [_adapter.validate_python(raw) for raw in modules]