"""An updated treeweaver implementation."""

# pylint: disable=too-few-public-methods

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import parse
import yaml

from tabular import Table, Tables

PathType = Union[Path, str]
ValueType = Union[str, list, dict, bool, int, float, None]  # Entity values


# Parse formatters
def underscored(string: str):
    """Parse formatter that converts blanks to underscore."""
    return string.replace(" ", "_")


def escaped(string: str):
    """Parse formatter that converts blanks to %-encoded."""
    # Alternatively we could use urllib.parse.quote()
    return string.replace(" ", "%20")


def xstrip(string: str):
    """Strip file extension and replace blanks with underscore."""
    return re.sub(r"\.\w+$", "", string).replace(" ", "_")


underscored.pattern = "[^/]+"  # type: ignore[attr-defined]
escaped.pattern = "[^/]+"  # type: ignore[attr-defined]
parse_formatters = {
    "underscored": underscored,
    "escaped": escaped,
    "xstrip": xstrip,
}


class Entity:
    """An entity to be documented.

    Arguments:
        name: Name of the entity, e.g. dataset.
        templates: Dict mapping keywords to template strings.

    """

    def __init__(self, name: str, templates: dict[str, str]) -> None:
        self.name = name
        self.templates = templates

    def substitute(self, env: dict) -> dict:
        """Return a JSON-LD dict documenting an individual by
        performing wildcard substitution of the `templates` attribute.

        """
        doc = {}
        for keyword, template in self.templates.items():
            if template:
                try:
                    if s := substitute(template, env):
                        doc[keyword] = s
                except KeyError as exc:
                    raise KeyError(  # pylint: disable=raise-missing-from
                        f"Variable '{exc}' in template for '{keyword}' is not "
                        f"assigned in pattern for entity: '{self.name}'"
                    )
        return doc


class Pattern:
    """Represents a pattern with additional metadata.

    Arguments:
        pattern: Wildcard pattern a directory or file path.
        entities: Dict mapping entity names to Entity instances.
        env_updates: Updates to the environment.

    """

    def __init__(
        self, pattern: str, entities: dict, env_updates: dict
    ) -> None:
        self.pattern = parse.compile(pattern, extra_types=parse_formatters)
        self.entities = {name: Entity(name, t) for name, t in entities.items()}
        self.env_updates = env_updates

    def document(self, path: PathType, env: dict) -> dict:
        """Document a directory or file path.

        Arguments:
            path: Directory or file path to document.
            env: Base environment for substitutions.

        Returns:
            A dict mapping entity names to JSON-LD documents.
            If `path` doesn't matche the pattern an empty dict is returned.
        """
        docs = {}
        if r := self.pattern.parse(str(path)):
            e = env.copy()
            e.update(r.named)
            p = Path(e.get("rootdir", ".")) / path
            if p.exists():
                ctime = datetime.fromtimestamp(p.stat().st_ctime).isoformat()
                mtime = datetime.fromtimestamp(p.stat().st_mtime).isoformat()
            else:
                ctime = mtime = ""
            e.setdefault("fullpath", str(p))
            e.setdefault("escapedpath", str(p).replace(" ", "%20"))
            e.setdefault("filename", p.name)
            e.setdefault("dirname", str(p.parent))
            e.setdefault("ctime", ctime)
            e.setdefault("mtime", mtime)
            e.setdefault("pattern", self.pattern.format)
            e.update(
                {k: substitute(v, e) for k, v in self.env_updates.items() if v}
            )
            for name, entity in self.entities.items():
                docs[name] = entity.substitute(e)
        return docs


class Treeweaver:
    """Class for documenting a directory structure."""

    def __init__(
        self,
        configfile: PathType,
        rootdir: Optional[PathType] = None,
    ) -> None:
        self.env: dict = {}
        self.entities: dict = {}
        self.patterns: list = []
        self.exclude: list = []
        newroot = Path(rootdir) if rootdir else Path(configfile).parent
        self.env["rootdir"] = str(newroot)
        self.parse_conf(configfile)

    def parse_conf(self, yamlfile: PathType) -> None:
        """Parses a treeweaver YAML configuration and updating the
        environment and entities, while replacing the patterns."""
        with open(yamlfile, "r", encoding="utf-8") as f:
            d = yaml.safe_load(f)
            self.env.update(d.get("environment", {}))
            self.entities.update(d.get("entities", {}))
            self.exclude.extend(d.get("exclude", ()))
            self.patterns = []
            for p in d.get("patterns", ()):
                pattern, updates = next(iter(p.items()))
                for entity, env in updates.items():
                    entities = {}
                    entities[entity] = self.entities.get(entity, {}).copy()
                    self.patterns.append(Pattern(pattern, entities, env))

    def document_path(self, path: PathType) -> dict:
        """Document a directory or file path.

        Arguments:
            path: Directory or file path to document.

        Returns:
            A dict mapping entity names to JSON-LD documents.
        """
        docs = defaultdict(list)
        for pattern in self.patterns:
            for k, v in pattern.document(path, self.env).items():
                docs[k].append(v)
        return dict(docs)

    def document(self, rootdir: PathType) -> dict:
        """Document a directory tree.

        Arguments:
            rootdir: Root directory of directory tree to document.

        Returns:
            A dict mapping entity names to JSON-LD documents.
        """
        root = Path(rootdir).resolve()
        docs = defaultdict(list)
        self.env["rootdir"] = root
        for path in root.rglob("*"):
            skip = False
            for exclude_pattern in self.exclude:
                if path.match(exclude_pattern):
                    skip = True
            if not skip:
                relpath = path.relative_to(root)
                for k, v in self.document_path(relpath).items():
                    docs[k].extend(v)
        return dict(docs)

    def totables(self, rootdir: PathType) -> Tables:
        """Create table documentation of directory tree.

        Processes all entities from the documented directory tree and
        converts them into a Tables collection for export or further
        processing.

        Arguments:
            rootdir: Root directory of the directory tree to document.

        Returns:
            A Tables object containing one table per entity type.
        """
        tables = Tables()
        for entity, docs in self.document(rootdir).items():
            table = totable(docs, name=entity)
            tables.append_table(table)
        return tables

    def savedoc(
        self,
        rootdir: PathType,
        path: PathType,
        fmt: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Document a directory tree and save created tables to file.

        Documents a directory tree and writes the results to a file
        in the specified format (or inferred from the file extension).

        Arguments:
            rootdir: Root directory of the directory tree to document.
            path: Output file path. Format is inferred from the file extension
                unless explicitly provided via `fmt`.
            fmt: Optional explicit format specifier (e.g., 'csv', 'xlsx',
                'json'). If not provided, format is inferred from the `path`
                extension.
            **kwargs: Additional keyword arguments passed to the Tables.write()
                method.
        """
        tables = self.totables(rootdir)
        tables.write(path, fmt=fmt, **kwargs)


def totable(
    dicts: list,
    name: Optional[str] = None,
    unique_header: Optional[str] = "@id",
) -> Table:
    """Convert a list of dictionaries to a Table.

    Transforms a flat list of dictionaries into a Table object with
    consistent column ordering. Missing values in dictionaries are
    represented as None in their corresponding cells.

    Arguments:
        dicts: List of dictionaries to convert. All values should be
            JSON-compatible (str, int, float, bool, None, list, dict).
        name: Optional name for the resulting table. Defaults to None.
        unique_header: If given and there are more than one row whos
            value in the column with header equal to `unique_header`,
            then only the first of these rows will be included in the table.

    Returns:
        A Table object with headers from all unique keys across the input
        dictionaries, and rows in the order of the input list.
    """
    headers: dict = {}  # use dict instead of set to keep ordering
    dicts = list(dicts)  # in case dicts is a iterator
    rows = []

    for d in dicts:
        for k in d.keys():
            headers[k] = None

    unique_values = set()
    for d in dicts:
        if unique_header and unique_header in d:
            unique_value = d[unique_header]
            if unique_value in unique_values:
                continue
            unique_values.add(unique_value)
        row = []
        for header in headers:
            row.append(d.get(header))
        rows.append(row)
    return Table(name=name, headers=list(headers.keys()), rows=rows)


def substitute(template: ValueType, env: dict) -> ValueType:
    """Return template with substitutions applied from `env`."""
    if isinstance(template, (bool, int, float, None.__class__)):
        return template
    if isinstance(template, (list, tuple)):
        return [substitute(element, env) for element in template if element]
    if isinstance(template, dict):
        return {k: substitute(v, env) for k, v in template.items()}
    return template.format(**env) if template else None
