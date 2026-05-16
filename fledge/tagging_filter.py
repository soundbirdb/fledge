"""Utility helpers: filter a list of job names using tag expressions."""
from __future__ import annotations

from typing import List, Optional

from fledge.tagging import TagRegistry


def filter_jobs_by_tag(
    registry: TagRegistry,
    all_job_names: List[str],
    require_any: Optional[List[str]] = None,
    require_all: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> List[str]:
    """Return job names that satisfy the given tag constraints.

    Args:
        registry: populated TagRegistry.
        all_job_names: full list of job names to filter.
        require_any: keep jobs that have AT LEAST ONE of these tags.
        require_all: keep jobs that have ALL of these tags.
        exclude: remove jobs that have ANY of these tags.

    If none of require_any / require_all are supplied, all jobs pass
    the inclusion step (only exclusion is applied).
    """
    result = list(all_job_names)

    if require_any:
        result = [
            name for name in result
            if registry.tags_for(name) and
            bool(set(registry.tags_for(name)) & set(require_any))
        ]

    if require_all:
        required = set(require_all)
        result = [
            name for name in result
            if required <= set(registry.tags_for(name))
        ]

    if exclude:
        excluded_set = set(exclude)
        result = [
            name for name in result
            if not (set(registry.tags_for(name)) & excluded_set)
        ]

    return result


def parse_tag_expression(expr: str) -> dict:
    """Parse a simple tag expression string into filter kwargs.

    Syntax:
        ``etl,nightly``          -> require_any=["etl", "nightly"]
        ``+etl +nightly``        -> require_all=["etl", "nightly"]
        ``etl -critical``        -> require_any=["etl"], exclude=["critical"]
    """
    require_any: List[str] = []
    require_all: List[str] = []
    exclude: List[str] = []

    for token in expr.split():
        token = token.strip()
        if not token:
            continue
        if token.startswith("+"):
            require_all.append(token[1:])
        elif token.startswith("-"):
            exclude.append(token[1:])
        else:
            # bare tokens separated by commas
            for t in token.split(","):
                t = t.strip()
                if t:
                    require_any.append(t)

    return {
        "require_any": require_any or None,
        "require_all": require_all or None,
        "exclude": exclude or None,
    }
