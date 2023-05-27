import abc
import pathlib
from typing import Any, Dict, List, Optional, Type, Union

from typing_extensions import Annotated, Literal

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

import dpath
import whoosh
from flask import Config
from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel, ConstrainedStr, Extra, Field, NonNegativeInt, ValidationError,
    validator)

# pylint: disable=too-few-public-methods

# Note: To preserve field ordering in Pydantic models, we annotate an
# attribute's type even when it could be determined by its default value.
# See https://docs.pydantic.dev/latest/usage/models/#field-ordering


class SlugStr(ConstrainedStr):

    regex = r'^[a-z][a-z0-9_\-]*$'


class FieldNameStr(ConstrainedStr):

    regex = r'^[a-z][a-zA-Z0-9_]*$'


class ElementIdStr(ConstrainedStr):

    regex = r'^[a-z][a-zA-Z0-9]*$'


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
    download_citations_link: bool
    download_citations_max_count: bool
    open_in_zotero_app: bool
    open_in_zotero_web: bool
    print_citations_link: bool
    print_citations_max_count: bool
    print_item_link: bool
    relations_links: bool
    relations_initial_limit: int = Field(ge=5)
    relations_sort: SlugStr  # TODO:config: Check that value is a valid Composer sort.
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
    fields: List[FieldNameStr]  # TODO:config: Check that values are valid Composer fields.
    max_days: NonNegativeInt
    require_any: Dict[FieldNameStr, List[Union[str, bool, int, float]]]  # TODO:config: Check that keys match valid Composer fields.
    reject_any: Dict[FieldNameStr, List[Union[str, bool, int, float]]]  # TODO:config: Check that keys match valid Composer fields.


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


class TemplatesModel(BaseModel):
    """Model for the kerko.templates config table."""

    class Config:
        extra = Extra.forbid

    base: str
    layout: str
    search: str
    search_item: str
    item: str
    atom_feed: str


class ZoteroModel(BaseModel):
    """Model for the kerko.zotero config table."""

    class Config:
        extra = Extra.forbid

    batch_size: int = Field(ge=20)
    max_attempts: int = Field(ge=1)
    wait: int = Field(ge=120)
    csl_style: SlugStr
    locale: str = Field(regex=r'^[a-z]{2}-[A-Z]{2}$')
    item_include_re: str
    item_exclude_re: str
    tag_include_re: str
    tag_exclude_re: str
    child_include_re: str
    child_exclude_re: str
    attachment_mime_types: List[str]


class SearchModel(BaseModel):
    """Model for the kerko.search config table."""

    class Config:
        extra = Extra.forbid

    result_fields: List[FieldNameStr]  # TODO:config: Check that values are valid Composer fields
    fulltext: bool
    whoosh_language: str = Field(regex=r'^[a-z]{2,3}$')

    @validator('whoosh_language')
    def validate_whoosh_has_language(cls, v):  # pylint: disable=no-self-argument
        if not whoosh.lang.has_stemmer(v):
            raise ValueError(f"language '{v}' not supported by Whoosh")


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

    scopes: List[SlugStr]  # TODO:config: Check that values are valid Composer scopes.
    boost: float


class CoreOptionalSearchFieldModel(BaseModel):
    """Model for the kerko.search_fields.core.optional config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    scopes: List[SlugStr]  # TODO:config: Check that values are valid Composer scopes.
    boost: float


class ZoteroFieldModel(BaseModel):
    """Model for the kerko.search_fields.zotero config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    scopes: List[SlugStr]  # TODO:config: Check that values are valid Composer scopes.
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


class BaseFacetModel(BaseModel, abc.ABC):
    """Base model for the kerko.facets config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    filter_key: SlugStr
    weight: int = 0
    initial_limit: NonNegativeInt = 0
    initial_limit_leeway: NonNegativeInt = 2
    sort_by: List[FieldNameStr] = ["label"]  # TODO:config: Validate that values are valid Composer fields
    sort_reverse: bool = False
    item_view: bool = True


class TagFacetModel(BaseFacetModel):

    type: Literal["tag"]
    title: Optional[str]


class ItemTypeFacetModel(BaseFacetModel):
    type: Literal["item_type"]
    title: Optional[str]
    item_view: bool = False


class YearFacetModel(BaseFacetModel):
    type: Literal["year"]
    title: Optional[str]
    item_view: bool = False


class LinkFacetModel(BaseFacetModel):
    type: Literal["link"]
    title: Optional[str]
    item_view: bool = False


class CollectionFacetModel(BaseFacetModel):
    type: Literal["collection"]
    title: str
    collection_key: str = Field(regex=r'^[A-Z]{8}$')


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
    ], Field(discriminator='type')
]


class SortsModel(BaseModel):
    """Model for the kerko.sorts config table."""

    class Config:
        extra = Extra.forbid

    enabled: bool = True
    weight: int = 0
    label: Optional[str]


class CitationFormatsModel(BaseModel):
    """Model for the kerko.citation_formats config table."""

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


class KerkoModel(BaseModel):
    """Model for the kerko config table."""

    class Config:
        extra = Extra.forbid

    assets: AssetsModel
    features: FeaturesModel
    feeds: FeedsModel
    meta: MetaModel
    pagination: PaginationModel
    templates: TemplatesModel
    zotero: ZoteroModel
    search: SearchModel
    scopes: Dict[SlugStr, ScopesModel]
    search_fields: SearchFieldsModel
    facets: Dict[FieldNameStr, FacetModelUnion]
    sorts: Dict[SlugStr, SortsModel]
    citation_formats: Dict[SlugStr, CitationFormatsModel]
    relations: Dict[ElementIdStr, RelationsModel]


def load_toml(filename: Union[str, pathlib.Path]) -> Dict[str, Any]:
    """Load the content of a TOML file."""
    try:
        with open(filename, 'rb') as file:
            return tomllib.load(file)
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
    Retrieve an arbitrarily nested configuration setting.

    `path` is a string of keys separated by dots ('.') acting as hierarchical
    level separators.

    Unlike `dict.get()`, this provides no way of specifying a default value as
    all configuration settings are expected to already have a default.
    Consequently, passing an invalid `path` is considered a programming error
    (because a default was omitted) and will throw a `KeyError` exception.
    """
    return dpath.get(config, path, separator='.')


def config_set(config: Config, path: str, value: Any) -> None:
    """
    Set an arbitrarily nested configuration setting.

    `path` is a string of keys separated by dots ('.') acting as hierarchical
    level separators.
    """
    dpath.new(config, path, value, separator='.')


def validate_config(
    config: Config,
    key: str = 'kerko',
    model: Type[BaseModel] = KerkoModel,
) -> None:
    """
    Parse and validate a configuration to ensure the data is valid.

    This only validates the structure that's under the specified key.

    If some types are incorrect, they may be silently coerced into the expected
    types (strict typing is not enforced by the models).
    """
    if config.get(key):
        try:
            config_set(config, key, model.parse_obj(config[key]).dict())
        except ValidationError as e:
            raise RuntimeError(f"Invalid configuration. {e}") from e
