import pathlib
from abc import ABC, abstractmethod
from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated, Any, Optional, Union

import dpath
import whoosh
from flask import Config
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    RootModel,
    ValidationError,
    field_validator,
    model_validator,
)
from typing_extensions import Literal

from kerko.specs import (
    LinkByEndpointSpec,
    LinkByURLSpec,
    LinkGroupSpec,
    LinkSpec,
    PageLinkSpec,
    PageSpec,
)

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


# Note: To preserve field ordering in Pydantic models, we annotate an
# attribute's type even when it could be determined by its default value.
# See https://docs.pydantic.dev/latest/usage/models/#field-ordering

SlugStr = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_\-]*$")]
URLPathStr = Annotated[str, Field(pattern=r"^/[a-z0-9_\-/]*$")]
FieldNameStr = Annotated[str, Field(pattern=r"^[a-z][a-zA-Z0-9_]*$")]
ElementIdStr = Annotated[str, Field(pattern=r"^[a-z][a-zA-Z0-9]*$")]
IdentifierStr = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
ZoteroItemIdStr = Annotated[str, Field(pattern=r"^[A-Z0-9]{8}$")]


class AssetsModel(BaseModel):
    """Model for the kerko.assets config table."""

    model_config = ConfigDict(extra="forbid")

    bootstrap_version: str
    jquery_version: str
    popper_version: str
    with_jquery: bool
    with_popper: bool


class FeaturesModel(BaseModel):
    """Model for the kerko.features config table."""

    model_config = ConfigDict(extra="forbid")

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

    model_config = ConfigDict(extra="forbid")

    formats: list[Optional[Literal["atom"]]]
    fields: list[FieldNameStr]
    max_days: NonNegativeInt
    require_any: dict[FieldNameStr, list[Union[str, bool, int, float]]]
    reject_any: dict[FieldNameStr, list[Union[str, bool, int, float]]]


class MetaModel(BaseModel):
    """Model for the kerko.meta config table."""

    model_config = ConfigDict(extra="forbid")

    title: str
    highwirepress_tags: bool
    google_analytics_id: str


class PaginationModel(BaseModel):
    """Model for the kerko.pagination config table."""

    model_config = ConfigDict(extra="forbid")

    page_len: int = Field(ge=2)
    pager_links: int = Field(ge=2)


class BreadcrumbModel(BaseModel):
    """Model for the kerko.breadcrumb config table."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool
    include_current: bool
    text_max_length: NonNegativeInt
    text_max_length_leeway: NonNegativeInt


class TemplatesModel(BaseModel):
    """Model for the kerko.templates config table."""

    model_config = ConfigDict(extra="forbid")

    base: str
    layout: str
    search: str
    search_item: str
    item: str
    page: str
    atom_feed: str


class ZoteroModel(BaseModel):
    """Model for the kerko.zotero config table."""

    model_config = ConfigDict(extra="forbid")

    batch_size: int = Field(ge=20)
    max_attempts: int = Field(ge=1)
    wait: int = Field(ge=120)
    csl_style: str
    locale: str = Field(pattern=r"^[a-z]{2,3}-[A-Za-z]+$")
    item_include_re: str
    item_exclude_re: str
    tag_include_re: str
    tag_exclude_re: str
    child_include_re: str
    child_exclude_re: str
    attachment_mime_types: list[str]


class PerformanceModel(BaseModel):
    """Model for the kerko.performance config table."""

    model_config = ConfigDict(extra="forbid")

    whoosh_index_memory_limit: int = Field(ge=16)
    whoosh_index_processors: int = Field(ge=1)


class SearchModel(BaseModel):
    """Model for the kerko.search config table."""

    model_config = ConfigDict(extra="forbid")

    result_fields: list[FieldNameStr]
    fulltext: bool
    whoosh_language: str = Field(pattern=r"^[a-z]{2,3}$")

    @field_validator("whoosh_language")
    @classmethod
    def validate_whoosh_has_language(cls, v):
        if not whoosh.lang.has_stemmer(v):
            msg = f"language '{v}' not supported by Whoosh"
            raise ValueError(msg)
        return v


class ScopesModel(BaseModel):
    """Model for the kerko.scopes config table."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    selector_label: Optional[str] = None
    breadbox_label: Optional[str] = None
    help_text: Optional[str] = None
    weight: int = 0


class CoreRequiredSearchFieldModel(BaseModel):
    """Model for the kerko.search_fields.core.required config table."""

    model_config = ConfigDict(extra="forbid")

    scopes: list[SlugStr]
    boost: float


class CoreOptionalSearchFieldModel(BaseModel):
    """Model for the kerko.search_fields.core.optional config table."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    scopes: list[SlugStr]
    boost: float


class ZoteroFieldModel(BaseModel):
    """Model for the kerko.search_fields.zotero config table."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    scopes: list[SlugStr]
    analyzer: Literal["id", "text", "name"]
    boost: float


class CoreSearchFieldsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required: dict[FieldNameStr, CoreRequiredSearchFieldModel]
    optional: dict[FieldNameStr, CoreOptionalSearchFieldModel]


class SearchFieldsModel(BaseModel):
    """Base model for the kerko.search_fields config table."""

    model_config = ConfigDict(extra="forbid")

    core: CoreSearchFieldsModel
    zotero: dict[FieldNameStr, ZoteroFieldModel]


class BaseFacetModel(BaseModel, ABC):
    """Base model for the kerko.facets config table."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    filter_key: SlugStr
    weight: int = 0
    initial_limit: NonNegativeInt = 0
    initial_limit_leeway: NonNegativeInt = 2
    sort_by: list[Literal["label", "count"]] = ["label"]
    sort_reverse: bool = False
    item_view: bool = True


class TagFacetModel(BaseFacetModel):
    type: Literal["tag"]
    title: Optional[str] = None


class ItemTypeFacetModel(BaseFacetModel):
    type: Literal["item_type"]
    title: Optional[str] = None
    item_view: bool = False


class YearFacetModel(BaseFacetModel):
    type: Literal["year"]
    title: Optional[str] = None
    item_view: bool = False


class LanguageFacetModel(BaseFacetModel):
    type: Literal["language"]
    title: Optional[str] = None
    item_view: bool = False
    values_separator_re: str = Field(";", min_length=1)
    normalize: bool = True
    locale: str = Field("en", pattern=r"^[a-z]{2,3}(-[A-Za-z]+)?$")
    allow_invalid: bool = False


class LinkFacetModel(BaseFacetModel):
    type: Literal["link"]
    title: Optional[str] = None
    item_view: bool = False


class CollectionFacetModel(BaseFacetModel):
    type: Literal["collection"]
    title: str
    collection_key: str = Field(pattern=r"^[A-Z0-9]{8}$")


# Note: Discriminated unions ensure that a single unambiguous error gets
# reported when validation fails. Reference:
# https://docs.pydantic.dev/latest/usage/types/#discriminated-unions-aka-tagged-unions

FacetModelUnion = Annotated[
    Union[
        TagFacetModel,
        ItemTypeFacetModel,
        YearFacetModel,
        LanguageFacetModel,
        LinkFacetModel,
        CollectionFacetModel,
    ],
    Field(discriminator="type"),
]


class SortsModel(BaseModel):
    """Model for the kerko.sorts config table."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    weight: int = 0
    label: Optional[str] = None


class BibFormatsModel(BaseModel):
    """Model for the kerko.bib_formats config table."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    weight: int = 0
    label: Optional[str] = None
    help_text: Optional[str] = None
    extension: SlugStr
    mime_type: str


class RelationsModel(BaseModel):
    """Model for the kerko.relations config table."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    weight: int = 0
    label: Optional[str] = None


class PageModel(BaseModel):
    """Model for items under the kerko.pages config table."""

    model_config = ConfigDict(extra="forbid")

    path: URLPathStr
    item_id: ZoteroItemIdStr
    title: str

    def to_spec(self) -> PageSpec:
        return PageSpec(
            path=self.path,
            item_id=self.item_id,
            title=self.title,
        )


class PagesModel(RootModel):
    """
    Model for the kerko.pages config table.

    The dictionary key will serve as the page's endpoint name, hence the
    constrained `IdentifierStr` type.
    """

    root: dict[IdentifierStr, PageModel]

    def to_spec(self) -> dict[str, PageSpec]:
        return {key: page_model.to_spec() for key, page_model in self.root.items()}


class LinkModel(BaseModel, ABC):
    model_config = ConfigDict(extra="forbid")

    text: str
    weight: int = 0
    new_window: bool = False

    @abstractmethod
    def to_spec(self) -> LinkSpec:
        pass


class LinkByEndpointModel(LinkModel):
    """Model for endpoint items under the kerko.link_groups config table."""

    type: Literal["endpoint"]
    endpoint: str
    anchor: Optional[str] = None
    scheme: Optional[str] = None
    external: bool = False
    parameters: Optional[dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_scheme(self):
        if self.scheme and not self.external:
            msg = "When specifying 'scheme', 'external' must be true."
            raise ValueError(msg)
        return self

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

    type: Literal["url"]
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

    type: Literal["page"]
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


class LinkGroupsModel(RootModel):
    root: dict[SlugStr, Annotated[list[LinkModelUnion], Field(min_items=1)]]

    def to_spec(self) -> dict[str, LinkGroupSpec]:
        return {
            key: LinkGroupSpec(key, [link_model.to_spec() for link_model in links])
            for key, links in self.root.items()
        }


class KerkoModel(BaseModel):
    """Model for the kerko config table."""

    model_config = ConfigDict(extra="forbid")

    assets: AssetsModel
    features: FeaturesModel
    feeds: FeedsModel
    meta: MetaModel
    pagination: PaginationModel
    breadcrumb: BreadcrumbModel
    pages: Optional[PagesModel] = None
    link_groups: LinkGroupsModel
    templates: TemplatesModel
    zotero: ZoteroModel
    performance: PerformanceModel
    search: SearchModel
    scopes: dict[SlugStr, ScopesModel]
    search_fields: SearchFieldsModel
    facets: dict[FieldNameStr, FacetModelUnion]
    sorts: dict[SlugStr, SortsModel]
    bib_formats: dict[SlugStr, BibFormatsModel]
    relations: dict[ElementIdStr, RelationsModel]


class ConfigModel(BaseModel):
    """Model for validating mandatory at the root config table."""

    # Note: This model allows extra fields since we cannot cover all variables
    # that Flask, Flask extensions, and applications might support.

    model_config = ConfigDict(coerce_numbers_to_str=True)

    SECRET_KEY: str = Field(min_length=12)
    ZOTERO_API_KEY: str = Field(min_length=16)
    ZOTERO_LIBRARY_ID: str = Field(pattern=r"^[0-9]+$")
    ZOTERO_LIBRARY_TYPE: Literal["user", "group"]
    kerko: Optional[KerkoModel] = None


def load_toml(filename: Union[str, pathlib.Path], verbose=False) -> dict[str, Any]:
    """Load the content of a TOML file."""
    try:
        with pathlib.Path(filename).open("rb") as file:
            config = tomllib.load(file)
            if verbose:
                print(f" * Loading configuration file {filename}")  # noqa: T201
            return config
    except OSError as e:
        msg = f"Unable to open TOML file.\n{e}"
        raise RuntimeError(msg) from e
    except tomllib.TOMLDecodeError as e:
        msg = f"Invalid TOML format in file '{filename}'.\n{e}"
        raise RuntimeError(msg) from e


def config_update(config: Config, new_data: dict[str, Any]) -> None:
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
    model: type[BaseModel] = ConfigModel,
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
            parsed = model.model_validate(config)
            config.update(parsed.model_dump())
            config["kerko_config"] = parsed
        elif config.get(key):
            # The parsed models are stored in the config as dicts. This way, the
            # whole configuration structure is made of dicts only, allowing
            # consistent access for any element at any depth.
            parsed = model.model_validate(config[key])
            config_set(config, key, parsed.model_dump())
            config[f"kerko_config.{key}"] = parsed
    except ValidationError as e:
        msg = f"Invalid configuration. {e}"
        raise RuntimeError(msg) from e


def is_toml_serializable(obj: object) -> bool:
    """
    Check if the given object would be serializable into a TOML file.

    This only performs a shallow check of the object.
    """
    return isinstance(
        obj, (bool, int, float, date, datetime, time, Decimal, str, list, tuple, dict)
    )
