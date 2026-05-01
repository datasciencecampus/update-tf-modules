from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter, model_validator

class BaseModule(BaseModel):
    name: str
    glob: str | None = None
    file: str | None = None
    files: list[str] | None = None

    @model_validator(mode="after")
    def validate_target_selector(self) -> "BaseModule":
        selectors = [
            self.glob is not None,
            self.file is not None,
            self.files is not None,
        ]
        if sum(selectors) != 1:
            raise ValueError(
                f"Module '{self.name}' must define exactly one of 'glob', 'file', or 'files'."
            )
        if self.files is not None and not self.files:
            raise ValueError(f"Module '{self.name}' has 'files' but it is empty.")
        return self

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

def parse_modules(raw_modules: list[dict[str, object]]) -> list[Module]:
    return [_adapter.validate_python(raw) for raw in raw_modules]