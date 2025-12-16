"""
Discovering dependencies between cached Zotero items and collections.
"""

from abc import ABC, abstractmethod

from karboni.database import schema as cache
from sqlalchemy import select
from sqlalchemy.orm import Session


class Discoverer(ABC):
    def __init__(self, cache_session: Session):
        self._cache_session = cache_session


class CollectionDependencyDiscoverer(Discoverer, ABC):
    @abstractmethod
    def discover(self, collection: cache.Collection) -> list[str]:
        pass


class CollectionAncestorsDiscoverer(CollectionDependencyDiscoverer):
    def __init__(self, *args, include_trashed=False, **kwargs):  # noqa: D417
        """
        Initialize.

        Args:
            include_trashed: Whether to include trashed collections in the discovered collections.
        """
        super().__init__(*args, **kwargs)
        self.include_trashed = include_trashed

    def discover(self, collection: cache.Collection) -> list[str]:
        """
        Retrieve the ancestors of a given collection.

        Args:
            collection: The collection whose ancestors are to be retrieved.

        Returns:
            A list of collection keys representing the path leading to the specified collection. The
            first list element is the root of the path. The specified collection is included at the
            end of the list, unless it doesn't exists, in which case an empty list is returned.
        """
        stmt = select(cache.Collection).where(
            cache.Collection.collection_key == collection.collection_key
        )
        if not self.include_trashed:
            stmt = stmt.where(cache.Collection.trashed.is_not(True))
        if not self._cache_session.scalar(stmt):
            return []

        current = collection.collection_key
        ancestors = [current]
        while current:
            stmt = select(cache.Collection).where(cache.Collection.collection_key == current)
            result = self._cache_session.scalar(stmt)
            if not self.include_trashed and result.trashed:
                return []
            current = result.parent_collection
            if current:
                ancestors.insert(0, current)  # Prepend to the list.

        return ancestors


class ItemDependencyDiscoverer(Discoverer, ABC):
    @abstractmethod
    def discover(self, item: cache.Item) -> list[str]:
        pass


class ItemSelfDiscoverer(ItemDependencyDiscoverer):
    def discover(self, item: cache.Item) -> list[str]:
        return [item.item_key]


class ItemParentDiscoverer(ItemDependencyDiscoverer):
    def discover(self, item: cache.Item) -> list[str]:
        return [item.parent_item] if item.parent_item else []


class ItemChildrenDiscoverer(ItemDependencyDiscoverer):
    def discover(self, item: cache.Item) -> list[str]:
        stmt = select(cache.Item.item_key).where(cache.Item.parent_item == item.item_key)
        return list(self._cache_session.scalars(stmt).all())


class ItemCollectionsDiscoverer(ItemDependencyDiscoverer):
    def __init__(self, *args, include_trashed=False, **kwargs):  # noqa: D417
        """
        Initialize.

        Args:
            include_trashed: Whether to include trashed collections in the discovered collections.
        """
        super().__init__(*args, **kwargs)
        self.include_trashed = include_trashed

    def discover(self, item: cache.Item) -> list[str]:
        """
        Retrieve the collections an item belongs to, including all of their ancestors.

        Args:
            item: The item whose collections are to be retrieved.

        Returns:
            A list of collection keys representing all collections the item belongs to, including
            ancestor collections.
        """
        discoverer = CollectionAncestorsDiscoverer(
            self._cache_session, include_trashed=self.include_trashed
        )
        collections = set()  # Use a set to avoid duplicates.
        for collection in item.collections:
            collections |= set(discoverer.discover(collection))
        return list(collections)


# TODO:R5770: Implement discoverer for updating item on fulltext changes.
