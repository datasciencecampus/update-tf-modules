from typing import Literal, NotRequired, TypedDict

class BaseTarget(TypedDict, total=False):
    file: str
    files: list[str]
    glob: str


class BaseCommon(TypedDict):
    name: str


class GitHubModule(BaseTarget, BaseCommon):
    type: Literal["github"]
    repo: str
    source_prefix: str
    lookup: NotRequired[Literal["release", "tag"]]
    pin: NotRequired[Literal["sha", "tag"]]


class RegistryModule(BaseTarget, BaseCommon):
    type: Literal["registry"]
    source: str

ModuleDef = GitHubModule | RegistryModule