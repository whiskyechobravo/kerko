import pathlib
from abc import ABC, abstractmethod
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type, Union

from typing_extensions import Annotated, Literal

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import dpath
import whoosh
from flask import Config
from pydantic import (
    BaseModel,
    ConstrainedStr,
    Extra,
    Field,
    NonNegativeInt,
    ValidationError,
    root_validator,
    validator,
)

from kerko.specs import (
    LinkByEndpointSpec,
    LinkByURLSpec,
    LinkGroupSpec,
    LinkSpec,
    PageLinkSpec,
    PageSpec,
)

# Note: To preserve field ordering in Pydantic models, we annotate an
# attribute's type even when it could be determined by its default value.
# See https://docs.pydantic.dev/latest/usage/models/#field-ordering


class SlugStr(ConstrainedStr):
    regex = r"^[a-z][a-z0-9_\-]*$"


class URLPathStr(ConstrainedStr):
    regex = r"^/[a-z0-9_\-/]*$"


class FieldNameStr(ConstrainedStr):
    regex = r"^[a-z][a-zA-Z0-9_]*$"


class ElementIdStr(ConstrainedStr):
    regex = r"^[a-z][a-zA-Z0-9]*$"


class IdentifierStr(ConstrainedStr):
    regex = r"^[a-z][a-z0-9_]*$"


class ZoteroItemIdStr(ConstrainedStr):
    regex = r"^[A-Z0-9]{8}$"


class AssetsModel(BaseModel):
    """Model for the kerko.assets config table."""

    class Config:
        extra = Extra.forbid

    bootstrap_version: str
    jquery_version: str
    popper_version: str
    with_jquery: bool
    with_popper: bool


class FeaturesModel(BaseModel):
    """Model for the kerko.features config table."""

    class Config:
        extra = Extra.forbid

    download_attachment_new_window: bool
    download_item: bool
    download_results: bool
    download_results_max_count: NonNegativeInt
    open_in_zotero_app: bool
    open_in_zotero_web: bool
    print_item: bool
    print_results: bool
    print_results_max_count: NonNegativeInt
    relations_links: bool
    relations_initial_limit: int = Field(ge=5)
    relations_sort: SlugStr
    results_abstracts: bool
    results_abstracts_max_length: NonNegativeInt
    results_abstracts_max_length_leeway: NonNegativeInt
    results_abstracts_toggler: bool
    results_attachment_links: bool
    results_url_links: bool


class FeedsModel(BaseModel):
    """Model for the kerko.feeds config table."""

    class Config:
        extra = Extra.forbid

    formats: List[Optional[Literal["atom"]]]
    fields: List[FieldNameStr]
    max_days: NonNegativeInt
    require_any: Dict[FieldNameStr, List[Union[str, bool, int, float]]]
    reject_any: Dict[FieldNameStr, List[Union[str, bool, int, float]]]


class MetaModel(BaseModel):
    """Model for the kerko.meta config table."""

    class Config:
        extra = Extra.forbid

    title: str
    highwirepress_tags: bool
    google_analytics_id: str


class PaginationModel(BaseModel):
    """Model for the kerko.pagination config table."""

    class Config:
        extra = Extra.forbid

    page_len: int = Field(ge=2)
    pager_links: int = Field(ge=2)


class BreadcrumbModel(BaseModel):
    """Model for the kerko.breadcrumb config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool
    include_current: bool
    text_max_length: NonNegativeInt
    text_max_length_leeway: NonNegativeInt


class TemplatesModel(BaseModel):
    """Model for the kerko.templates config table."""

    class Config:
        extra = Extra.forbid

    base: str
    layout: str
    search: str
    search_item: str
    item: str
    page: str
    atom_feed: str


class ZoteroModel(BaseModel):
    """Model for the kerko.zotero config table."""

    class Config:
        extra = Extra.forbid

    batch_size: int = Field(ge=20)
    max_attempts: int = Field(ge=1)
    wait: int = Field(ge=120)
    csl_style: str
    locale: str = Field(regex=r"^[a-z]{2}-[A-Z]{2}$")
    item_include_re: str
    item_exclude_re: str
    tag_include_re: str
    tag_exclude_re: str
    child_include_re: str
    child_exclude_re: str
    attachment_mime_types: List[str]


class PerformanceModel(BaseModel):
    """Model for the kerko.performance config table."""

    class Config:
        extra = Extra.forbid

    whoosh_index_memory_limit: int = Field(ge=16)
    whoosh_index_processors: int = Field(ge=1)


class SearchModel(BaseModel):
    """Model for the kerko.search config table."""

    class Config:
        extra = Extra.forbid

    result_fields: List[FieldNameStr]
    fulltext: bool
    whoosh_language: str = Field(regex=r"^[a-z]{2,3}$")

    @validator("whoosh_language")
    def validate_whoosh_has_language(cls, v):  # noqa: N805
        if not whoosh.lang.has_stemmer(v):
            raise ValueError(f"language '{v}' not supported by Whoosh")
        return v


class ScopesModel(BaseModel):
    """Model for the kerko.scopes config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    selector_label: Optional[str]
    breadbox_label: Optional[str]
    help_text: Optional[str]
    weight: int = 0


class CoreRequiredSearchFieldModel(BaseModel):
    """Model for the kerko.search_fields.core.required config table."""

    class Config:
        extra = Extra.forbid

    scopes: List[SlugStr]
    boost: float


class CoreOptionalSearchFieldModel(BaseModel):
    """Model for the kerko.search_fields.core.optional config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    scopes: List[SlugStr]
    boost: float


class ZoteroFieldModel(BaseModel):
    """Model for the kerko.search_fields.zotero config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    scopes: List[SlugStr]
    analyzer: Union[Literal["id"], Literal["text"], Literal["name"]]
    boost: float


class CoreSearchFieldsModel(BaseModel):
    class Config:
        extra = Extra.forbid

    required: Dict[FieldNameStr, CoreRequiredSearchFieldModel]
    optional: Dict[FieldNameStr, CoreOptionalSearchFieldModel]


class SearchFieldsModel(BaseModel):
    """Base model for the kerko.search_fields config table."""

    class Config:
        extra = Extra.forbid

    core: CoreSearchFieldsModel
    zotero: Dict[FieldNameStr, ZoteroFieldModel]


class BaseFacetModel(BaseModel, ABC):
    """Base model for the kerko.facets config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    filter_key: SlugStr
    weight: int = 0
    initial_limit: NonNegativeInt = 0
    initial_limit_leeway: NonNegativeInt = 2
    sort_by: List[Union[Literal["label"], Literal["count"]]] = ["label"]
    sort_reverse: bool = False
    item_view: bool = True


class TagFacetModel(BaseFacetModel):
    type: Literal["tag"]  # noqa: A003
    title: Optional[str]


class ItemTypeFacetModel(BaseFacetModel):
    type: Literal["item_type"]  # noqa: A003
    title: Optional[str]
    item_view: bool = False


class YearFacetModel(BaseFacetModel):
    type: Literal["year"]  # noqa: A003
    title: Optional[str]
    item_view: bool = False


class LinkFacetModel(BaseFacetModel):
    type: Literal["link"]  # noqa: A003
    title: Optional[str]
    item_view: bool = False


class CollectionFacetModel(BaseFacetModel):
    type: Literal["collection"]  # noqa: A003
    title: str
    collection_key: str = Field(regex=r"^[A-Z0-9]{8}$")


# Note: Discriminated unions ensure that a single unambiguous error gets
# reported when validation fails. Reference:
# https://docs.pydantic.dev/latest/usage/types/#discriminated-unions-aka-tagged-unions

FacetModelUnion = Annotated[
    Union[
        TagFacetModel,
        ItemTypeFacetModel,
        YearFacetModel,
        LinkFacetModel,
        CollectionFacetModel,
    ],
    Field(discriminator="type"),
]


class SortsModel(BaseModel):
    """Model for the kerko.sorts config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    weight: int = 0
    label: Optional[str]


class BibFormatsModel(BaseModel):
    """Model for the kerko.bib_formats config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    weight: int = 0
    label: Optional[str]
    help_text: Optional[str]
    extension: SlugStr
    mime_type: str


class RelationsModel(BaseModel):
    """Model for the kerko.relations config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    weight: int = 0
    label: Optional[str]


class PageModel(BaseModel):
    """Model for items under the kerko.pages config table."""

    class Config:
        extra = Extra.forbid

    path: URLPathStr
    item_id: ZoteroItemIdStr
    title: str

    def to_spec(self) -> PageSpec:
        return PageSpec(
            path=self.path,
            item_id=self.item_id,
            title=self.title,
        )


class PagesModel(BaseModel):  # TODO: Pydantic v2: inherit RootModel.
    """
    Model for the kerko.pages config table.

    The dictionary key will serve as the page's endpoint name, hence the
    constrained `IdentifierStr` type.
    """

    __root__: Dict[IdentifierStr, PageModel]

    def to_spec(self) -> Dict[str, PageSpec]:
        return {key: page_model.to_spec() for key, page_model in self.__root__.items()}


class LinkModel(BaseModel, ABC):
    class Config:
        extra = Extra.forbid

    text: str
    weight: int = 0
    new_window: bool = False

    @abstractmethod
    def to_spec(self) -> LinkSpec:
        pass


class LinkByEndpointModel(LinkModel):
    """Model for endpoint items under the kerko.link_groups config table."""

    type: Literal["endpoint"]  # noqa: A003
    endpoint: str
    anchor: Optional[str]
    scheme: Optional[str]
    external: bool = False
    parameters: Optional[Dict[str, Any]]

    @root_validator
    def validate_scheme(cls, values):  # noqa: N805
        if values.get("scheme") and not values.get("external"):
            raise ValueError("When specifying 'scheme', 'external' must be true.")
        return values

    def to_spec(self) -> LinkSpec:
        return LinkByEndpointSpec(
            text=self.text,
            weight=self.weight,
            new_window=self.new_window,
            endpoint=self.endpoint,
            anchor=self.anchor,
            scheme=self.scheme,
            external=self.external,
            parameters=self.parameters,
        )


class LinkByURLModel(LinkModel):
    """Model for URL items under the kerko.link_groups config table."""

    type: Literal["url"]  # noqa: A003
    url: str  # TODO: Validate as URL string

    def to_spec(self) -> LinkSpec:
        return LinkByURLSpec(
            text=self.text,
            weight=self.weight,
            new_window=self.new_window,
            url=self.url,
        )


class PageLinkModel(LinkModel):
    """Model for page items under the kerko.link_groups config table."""

    type: Literal["page"]  # noqa: A003
    page: str

    def to_spec(self) -> LinkSpec:
        return PageLinkSpec(
            text=self.text,
            weight=self.weight,
            page=self.page,
        )


LinkModelUnion = Annotated[
    Union[
        LinkByEndpointModel,
        LinkByURLModel,
        PageLinkModel,
    ],
    Field(discriminator="type"),
]


class LinkGroupsModel(BaseModel):  # TODO: Pydantic v2: inherit RootModel.
    __root__: Dict[SlugStr, Annotated[List[LinkModelUnion], Field(min_items=1)]]

    def to_spec(self) -> Dict[str, LinkGroupSpec]:
        return {
            key: LinkGroupSpec(key, [link_model.to_spec() for link_model in links])
            for key, links in self.__root__.items()
        }


class KerkoModel(BaseModel):
    """Model for the kerko config table."""

    class Config:
        extra = Extra.forbid

    assets: AssetsModel
    features: FeaturesModel
    feeds: FeedsModel
    meta: MetaModel
    pagination: PaginationModel
    breadcrumb: BreadcrumbModel
    pages: Optional[PagesModel]
    link_groups: LinkGroupsModel
    templates: TemplatesModel
    zotero: ZoteroModel
    performance: PerformanceModel
    search: SearchModel
    scopes: Dict[SlugStr, ScopesModel]
    search_fields: SearchFieldsModel
    facets: Dict[FieldNameStr, FacetModelUnion]
    sorts: Dict[SlugStr, SortsModel]
    bib_formats: Dict[SlugStr, BibFormatsModel]
    relations: Dict[ElementIdStr, RelationsModel]


class ConfigModel(BaseModel):
    """Model for validating mandatory at the root config table."""

    # Note: This model allows extra fields since we cannot cover all variables
    # that Flask, Flask extensions, and applications might support.

    SECRET_KEY: str = Field(min_length=12)
    ZOTERO_API_KEY: str = Field(min_length=16)
    ZOTERO_LIBRARY_ID: str = Field(regex=r"^[0-9]+$")
    ZOTERO_LIBRARY_TYPE: Union[Literal["user"], Literal["group"]]
    kerko: Optional[KerkoModel]


def load_toml(filename: Union[str, pathlib.Path], verbose=False) -> Dict[str, Any]:
    """Load the content of a TOML file."""
    try:
        with open(filename, "rb") as file:
            config = tomllib.load(file)
            if verbose:
                print(f" * Loading configuration file {filename}")  # noqa: T201
            return config
    except OSError as e:
        raise RuntimeError(f"Unable to open TOML file.\n{e}") from e
    except tomllib.TOMLDecodeError as e:
        raise RuntimeError(f"Invalid TOML format in file '{filename}'.\n{e}") from e


def config_update(config: Config, new_data: Dict[str, Any]) -> None:
    """
    Update the configuration with the specified `dict`.

    Unlike the standard `dict.update`, this performs a deep merge. However, it
    does not deep copy the objects.
    """
    dpath.merge(config, new_data, flags=dpath.MergeType.REPLACE)


def config_get(config: Config, path: str) -> Any:
    """
    Retrieve an arbitrarily nested configuration parameter.

    `path` is a string of keys separated by dots ('.') acting as hierarchical
    level separators.

    Unlike `dict.get()`, this provides no way of specifying a default value as
    all configuration parameters are expected to have be already initialized
    with a default value. Passing an invalid `path`, i.e., trying to access a
    parameter that does not have a value, is considered a programming error and
    will throw a `KeyError` exception.
    """
    return dpath.get(config, path, separator=".")


def config_set(config: Config, path: str, value: Any) -> None:
    """
    Set an arbitrarily nested configuration parameter.

    `path` is a string of keys separated by dots ('.') acting as hierarchical
    level separators.
    """
    dpath.new(config, path, value, separator=".")


def parse_config(
    config: Config,
    key: Optional[str] = None,
    model: Type[BaseModel] = ConfigModel,
) -> None:
    """
    Parse and validate configuration using `model`.

    Configuration values in the `config` object get replaced by validated ones.
    Values may thus get silently coerced into the types specified by the model
    (unless strict typing is enforced by the model, in which case an error will
    be raised).

    This function also inserts a parsed representation of the configuration
    under key 'kerko_config'.

    If `key` is `None`, then the whole configuration gets parsed with the given
    `model`. Otherwise only the structure at the specified `key` gets parsed.

    If `key` is not `None` but is absent from the config, parsing is silently
    skipped.
    """
    try:
        if key is None:
            parsed = model.parse_obj(config)
            config.update(parsed.dict())
            config["kerko_config"] = parsed
        elif config.get(key):
            # The parsed models are stored in the config as dicts. This way, the
            # whole configuration structure is made of dicts only, allowing
            # consistent access for any element at any depth.
            parsed = model.parse_obj(config[key])
            config_set(config, key, parsed.dict())
            config[f"kerko_config.{key}"] = parsed
    except ValidationError as e:
        raise RuntimeError(f"Invalid configuration. {e}") from e


def is_toml_serializable(obj: object) -> bool:
    """
    Check if the given object would be serializable into a TOML file.

    This only performs a shallow check of the object.
    """
    return isinstance(
        obj, (bool, int, float, date, datetime, time, Decimal, str, list, tuple, dict)
    )
