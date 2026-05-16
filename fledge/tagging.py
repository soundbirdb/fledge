"""Job tagging — attach metadata tags to jobs and filter/query by them."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set


@dataclass
class TagPolicy:
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "TagPolicy":
        raw = data.get("tags", [])
        if isinstance(raw, str):
            tags = [t.strip() for t in raw.split(",") if t.strip()]
        else:
            tags = [str(t).strip() for t in raw if str(t).strip()]
        return cls(tags=tags)

    @property
    def enabled(self) -> bool:
        return bool(self.tags)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def matches_any(self, tags: Iterable[str]) -> bool:
        return bool(self.tag_set & set(tags))

    def matches_all(self, tags: Iterable[str]) -> bool:
        return set(tags) <= self.tag_set

    @property
    def tag_set(self) -> Set[str]:
        return set(self.tags)


class TagRegistry:
    """Maps job names to their TagPolicy; supports querying jobs by tag."""

    def __init__(self) -> None:
        self._registry: Dict[str, TagPolicy] = {}

    def register(self, job_name: str, policy: TagPolicy) -> None:
        self._registry[job_name] = policy

    def tags_for(self, job_name: str) -> List[str]:
        policy = self._registry.get(job_name)
        return policy.tags if policy else []

    def jobs_with_tag(self, tag: str) -> List[str]:
        return [
            name
            for name, policy in self._registry.items()
            if policy.has_tag(tag)
        ]

    def jobs_matching_any(self, tags: Iterable[str]) -> List[str]:
        tag_list = list(tags)
        return [
            name
            for name, policy in self._registry.items()
            if policy.matches_any(tag_list)
        ]

    def jobs_matching_all(self, tags: Iterable[str]) -> List[str]:
        tag_list = list(tags)
        return [
            name
            for name, policy in self._registry.items()
            if policy.matches_all(tag_list)
        ]

    def all_tags(self) -> Set[str]:
        result: Set[str] = set()
        for policy in self._registry.values():
            result |= policy.tag_set
        return result
