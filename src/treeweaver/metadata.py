"""Simple documentation demo."""

import fnmatch
import json
import os
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Iterator, Optional, Sequence, Union
from urllib.parse import unquote, urlsplit, urlunsplit

from tabular import Tables

PathType = Union[Path, str]
_cache: dict = {}  # Local cache


class ScopeVariable:
    """Represents a scope variable.

    Arguments:
        key: Variable name
        value: Variable value
        options: Options, see `parseopt()`
        comment: Comment
        path: Path to file in which this variable was defined

    """

    def __init__(
        self,
        key: str,
        value: Any,
        options: Optional[Union[str, dict]] = None,
        comment: Optional[str] = None,
        path: Optional[PathType] = None,
    ) -> None:
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        opts = parse_options(options)
        if "sep" in opts and isinstance(value, str):
            value = [jsontype(v) for v in value.split(opts["sep"])]
        else:
            value = jsontype(value)
        if "strip" in opts and opts["strip"]:
            if isinstance(value, str):
                value = value.strip()
            elif isseq(value):
                value = [v.strip() if isinstance(v, str) else v for v in value]
        if "append" in opts and opts["append"]:
            if not isseq(value):
                value = [value]
        self.key = key
        self.value = value
        self.options = opts
        self.comment = comment
        self.path = Path(path) if path else None

    def __repr__(self) -> str:
        return (
            f"ScopeVariable(key={self.key!r}, value={self.value!r}, "
            f"options={self.options}, comment={self.comment!r}, path={self.path})"
        )

    def tolist(self) -> list:
        """Return a list variable key, value, options, comment and path."""
        return [self.key, self.value, self.options, self.comment, self.path]

    def copy(self) -> "ScopeVariable":
        """Return a copy of self."""
        return ScopeVariable(
            key=self.key,
            value=self.value,
            options=self.options,
            comment=self.comment,
            path=self.path,
        )


class Scope:
    """Class representing a scope."""

    def __init__(self):
        self._scope = {}

    def __getitem__(self, key: str) -> None:
        return self._scope[key].value

    def __contains__(self, key: str) -> bool:
        return key in self._scope

    def __iter__(self) -> Iterator:
        yield from self._scope

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Return value for `key` or `default` if `key` is not in scope."""
        return self._scope[key].value if key in self._scope else default

    def getoptions(self, key: str, default: Optional[dict] = None) -> dict:
        """Return options for `key`."""
        return (
            self._scope[key].options
            if key in self._scope
            else default if default else {}
        )

    def getcomment(
        self, key: str, default: Optional[str] = None
    ) -> Union[str, None]:
        """Return comment for `key`."""
        return self._scope[key].comment if key in self._scope else default

    def getpath(
        self, key: str, default: Optional[PathType] = None
    ) -> Union[Path, None]:
        """Return path for `key`."""
        return (
            self._scope[key].path
            if key in self._scope
            else Path(default) if default else None
        )

    def add(
        self,
        key: str,
        value: Any,
        options: Optional[dict] = None,
        comment: Optional[str] = None,
        path: Optional[PathType] = None,
    ) -> None:
        """Add variable (provided as key-value pair) to scope."""
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        var = ScopeVariable(
            key,
            value,
            options=options if options else self.getoptions(key),
            comment=comment if comment else self.getcomment(key),
            path=path if path else self.getpath(key),
        )
        if key in self._scope:
            if "append" in var.options and var.options["append"]:
                v = self[key]
                if not isseq(v):
                    v = [v]
                var.value = v + var.value
        self._scope[key] = var

    def update(self, other: "Scope") -> None:
        """Update self from other."""
        for v in other._scope.values():  # pylint: disable=protected-access
            self.add(*v.tolist())

    def copy(self) -> "Scope":
        """Return a copy of self."""
        new = self.__class__()
        for k, v in self._scope.items():
            new._scope[k] = v.copy()  # pylint: disable=protected-access
        return new

    def items(self):
        """Return an iterator over the of the scope items."""
        for key, v in self._scope.items():
            yield (key, v.value)

    def merge(self, filename: PathType, sheet=0, **kwargs) -> "Scope":
        """Return a new scope by merging the current scope with `filename`.
        The current scope is unchanged."""
        new = self.copy()
        other = self.fromfile(filename, sheet=sheet, **kwargs)
        new.update(other)
        return new

    @classmethod
    def fromfile(cls, filename: PathType, sheet=0, **kwargs) -> "Scope":
        """Return a new Scope from `filename`.

        Arguments:
            filename: Metadata file to parse.
            sheet: Sheet name or number (only relevant for Excel)
            kwargs: Keyword arguments passed to the parser.

        """
        tables = Tables()
        tables.append_file(filename, **kwargs)
        table = tables[sheet]
        new = cls()
        for row in table.rows:
            padded = row[:4] + [None] * min(5, 5 - len(row))
            padded[4] = Path(filename)
            new.add(*padded)
        return new

    @staticmethod
    def default_scope() -> "Scope":
        """Returns a new default scope."""
        if "default_scope" not in _cache:
            thisdir = Path(__file__).resolve().parent
            _cache["default_scope"] = Scope.fromfile(
                thisdir / "metadata_default.csv"
            )
        return _cache["default_scope"].copy()

    def _get_substitutions(self, path: PathType) -> dict:
        """Return substitution pattern for `path`."""
        p = Path(path)
        pathurl = ""
        if "_baseurl" in self:
            r = urlsplit(self["_baseurl"])
            root = Path(unquote(r.path))
            base = self.getpath("_baseurl").resolve().parent  # type: ignore
            newpath = str(root / p.resolve().relative_to((base).resolve()))
            # It seems that urllib.parse.quote() quotes too much
            # Just quote space
            quoted = newpath.replace(" ", "%20")
            components = (r.scheme, r.netloc, quoted, r.query, r.fragment)
            pathurl = urlunsplit(components)  # type: ignore
        d = {
            "_path": p,
            "_name": p.name,
            "_ctime": datetime.fromtimestamp(p.stat().st_ctime).isoformat(),
            "_mtime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
            "_pathurl": pathurl,
        }
        for k, v in self.items():
            d[k] = v
        return d

    def document(self, path: PathType) -> dict:
        """Return a dict documenting `path`."""
        subs = self._get_substitutions(path)
        d = {
            "@id": _substitute(subs.get("@id", "${_prefix}:${_path}"), subs),
            "@type": _substitute(subs.get("@type", "emmo:Dataset"), subs),
        }
        for k, v in self.items():
            if not k.startswith("_") and v:
                d[k] = _substitute(v, subs)
        return d


def _substitute(s: Any, subs: dict) -> Any:
    """Help function for substituting placeholders in `s` with `subs`."""
    if isinstance(s, str):
        return jsontype(Template(s).substitute(subs))
    if isinstance(s, Sequence):
        return [jsontype(Template(t).substitute(subs)) for t in s]
    return s


def isseq(v: Any) -> bool:
    """Return True if `v` is a sequence but not a string."""
    return isinstance(v, Sequence) and not isinstance(v, (str, bytes))


def parse_options(options: Union[str, dict, None]) -> dict:
    """Returns `options` as a dict."""
    if options is None:
        return {}
    if isinstance(options, dict):
        return options
    opts = {}
    for opt in options.split("&"):
        k, v = opt.split("=", 1)
        opts[k] = jsontype(v)
    return opts


def jsontype(value: str) -> Any:
    """Convert JSON string `value` to Python type."""
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def match(filename: str, patterns: Sequence):
    """Returns whether `filename` matches any wildcard pattern in `patterns`."""
    for pattern in patterns:
        if fnmatch.fnmatchcase(filename, pattern):
            return True
    return False


def docdir(rootdir: str, scope: Optional[Scope]) -> list:
    """Recursively documents a directory structure.

    Arguments:
        rootdir: Root of directory structure to document.
        scope: Scope

    Returns:
        List of dicts documenting all datasets in the directory structure.
    """
    metadata_pattern = "__METADATA__.*"
    scope = scope if scope else Scope.default_scope()
    ignored = [metadata_pattern]  # List of wildcard patterns to ignore
    doc = []

    try:
        with os.scandir(rootdir) as entries:
            for path in Path(rootdir).glob(metadata_pattern):
                scope = scope.merge(path)

            for entry in entries:
                if match(entry.name, ignored):
                    continue
                if entry.is_file():
                    doc.append(scope.document(entry.path))
                elif entry.is_dir():
                    doc.extend(docdir(entry.path, scope.copy()))
    except PermissionError:
        print(f"Permission denied: {rootdir}")

    return doc
