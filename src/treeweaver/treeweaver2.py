"""An updated treeweaver implementation."""

from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import parse
import yaml

PathType = Union[Path, str]
ValueType = Union[str, list, dict, bool, int, float, None]  # Entity values


class Entity:
    """An entity to be documented.

    Arguments:
        name: Name of the entity, e.g. dataset.
        templates: Dict mapping keywords to template strings.

    """

    # pylint: disable=too-few-public-methods

    def __init__(self, name: str, templates: dict[str, str]) -> None:
        self.name = name
        self.templates = templates

    def substitute(self, env: dict) -> dict:
        """Return a JSON-LD dict documenting an individual by
        performing with Perform wildcard substitution of the `templates`
        attribute.

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

    # pylint: disable=too-few-public-methods

    def __init__(
        self, pattern: str, entities: dict, env_updates: dict
    ) -> None:
        self.pattern = parse.compile(pattern)
        self.entities = {name: Entity(name, t) for name, t in entities.items()}
        self.env_updates = env_updates

    def document(self, path: PathType, env: dict) -> list:
        """Document a directory or file path.

        Arguments:
            path: Directory or file path to document.
            env: Base environment for substitutions.

        Returns:
            A list of JSON-LD documents if `path` matches this pattern.
            Otherwise an empty list is returned.
        """
        docs = []
        if r := self.pattern.parse(str(path)):
            e = env.copy()
            e.update(r.named)
            e.update(
                {k: substitute(v, e) for k, v in self.env_updates.items() if v}
            )
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
            for entity in self.entities.values():
                docs.append(entity.substitute(e))
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
        self.rootdir = Path(rootdir) if rootdir else Path(configfile).parent
        self.parse_conf(configfile)
        self.env["rootdir"] = str(self.rootdir)

    def parse_conf(self, yamlfile: PathType) -> None:
        """Parses a treeweaver YAML configuration and updating the
        environment and entities, while replacing the patterns."""
        with open(yamlfile, "r", encoding="utf-8") as f:
            d = yaml.safe_load(f)
            self.env.update(d.get("environment", {}))
            self.entities.update(d.get("entities", {}))
            self.patterns = []
            for p in d.get("patterns", ()):
                pattern, updates = next(iter(p.items()))
                for entity, env in updates.items():
                    entities = {}
                    entities[entity] = self.entities.get(entity, {}).copy()
                    self.patterns.append(Pattern(pattern, entities, env))

    def document(self, path: PathType) -> list:
        """Document a directory or file path.

        Arguments:
            path: Directory or file path to document.
            env: Base environment for substitutions.

        Returns:
            A list of JSON-LD documents if `path` matches this pattern.
            Otherwise an empty list is returned.
        """
        doc = []
        for pattern in self.patterns:
            doc.extend(pattern.document(path, self.env))
        return doc


def substitute(template: ValueType, env: dict) -> ValueType:
    """Return template with substitutions applied from `env`."""
    if isinstance(template, (bool, int, float, None.__class__)):
        return template
    if isinstance(template, (list, tuple)):
        return [substitute(element, env) for element in template if element]
    if isinstance(template, dict):
        return {k: substitute(v, env) for k, v in template.items()}
    return template.format(**env) if template else None
