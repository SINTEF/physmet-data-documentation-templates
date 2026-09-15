"""Support wildcard substitutions of values in the info.yaml file.

In the info.yaml file, one can write

```yaml

# Keywords starting with underscore will not be included in the
# generated documentation.
_prefix = "abc"                            # Prefix for my data namespace
_baseurl = "https://..."                   # URL to data root folder

# These keywords will be included in the generates documentation.
title: "${_name}"                          # expands to file name
rightsHolder: "org:SINTEF"
releaseDate: "${_ctime}"                   # expands to creation time
distribution.downloadURL: "${_pathurl}"    # expands to URL
description "Description of ${title}..."   # expands title to what is set above

```

Any defined keyword in the current scope can be referred to in a variable
substitution. The following calculated variables can also be used:

- **_path**: Relative path from root data directory (the directory with the
      info.yaml file defining `base_url`).
- **_name**: Final component of path.
- **_ctime**: Creation time (ISO format).
- **_mtime**: Modification time (ISO format).
- **_pathurl**: URL that can be used for `distribution.downloadURL`.
- **_parent**: IRI of the parent folder.


Example usage from Python:

```python
from pathlib import Path

from tripper import Triplestore
from tripper.datadoc import store
from treeweaver import Scope


datadir = Path("path/to/root/of/datadir")

s = Scope.frominfo(datadir / "info.yaml")
doc = s.document(datadir)  # TODO: Too be called from within treeweaver...

ts = Triplestore(backend="rdflib")
store(ts, doc, context=datadir / "context.json")

```


Options:
  - sep: Separator for cells with multiple values. Will be converted to a list.
  - append: Append to existing value using the argument as separator. If the
        argument is the empty string, turn off appending. Implies `sep` with
        given argument.
  - strip: Whether to strip leading and trailing whitespaces from cell values.
        [default=true]
  - recursive: Whether the value and options will be applied recursively to
        subfolders. [default=true]

"""

import fnmatch
import json
import os
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Iterator, Optional, Sequence, Union
from urllib.parse import unquote, urlsplit, urlunsplit

import yaml

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
        value: str,
        options: Optional[Union[str, dict]] = None,
        comment: Optional[str] = None,
        path: Optional[PathType] = None,
    ) -> None:

        self._value = None

        self.key = key
        self.options = parse_options(options)
        self.comment = comment
        self.path = Path(path) if path else None
        self.template = None  # assigned by the `value` property
        self.value = value  # assign value as the last thing we do

    def __repr__(self) -> str:
        return (
            f"ScopeVariable(key={self.key!r}, value={self.value!r}, "
            f"options={self.options}, comment={self.comment!r}, "
            f"path={self.path})"
        )

    _defaultsep = ";&|¦§^~%£@?"

    def _getsep(value: str):
        """Return separator character in `self.options`.

        If "sep" is not in `self.options`, assign it from the first
        character in `self._defaultsep` that is neither in
        `self.value` nor in `value`.
        """
        if "sep" not in self.options:
            for sep in self._defaultsep:
                notin = lambda sep, v: isinstance(v, str) and sep not in v
                if notin(sep, self._value) and notin(sep, value):
                    self.options["sep"] = sep
                    break
            else:
                raise ValueError(
                    "Not able to find a separator that is not used in a value."
                )
        return self.options["sep"]

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        if self.options.get("strip", True) and isinstance(value, str):
            value = value.strip()
        if self.options.get("append", False) and self.value:
            sep = self.options.get("sep")
            if sep in value:
                raise ValueError(
                    f"Cannot append value '{value}' containing sep: '{sep}'"
                )
            self._value += sep + value
        else:
            self._value = value
        self.template = Template(self._value) if self._value else None

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
        self.parent = None

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

    def gettemplate(
        self, key: str, default: Optional[Template] = None
    ) -> Union[Template, None]:
        """Return str.Template instance for `key`."""
        return self._scope[key].template if key in self._scope else default

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
        self._scope[key] = ScopeVariable(
            key,
            value,
            options=options if options else self.getoptions(key),
            comment=comment if comment else self.getcomment(key),
            path=path if path else self.getpath(key),
        )

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

    def merged(self, other: Scope) -> "Scope":
        """Return a new scope by merging the current scope with `other`.

        The current scope is unchanged."""
        new = self.copy()
        new.parent = self
        new.update(other)
        return new

    def new(self) -> "Scope":
        """Return a new scope starting from the cumment one.

        The only difference from copy(), is that new() assigns the `parent`
        attribute to `self`.
        """
        new = self.copy()
        new.parent = self
        return new

    @classmethod
    def fromtable(cls, filename: PathType, sheet=0, **kwargs) -> "Scope":
        """Return a new Scope from table `filename`.

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

    @classmethod
    def frominfo(cls, infofile: PathType) -> "Scope":
        """Return a new Scope from yaml file `infofile`."""
        special_keys = set(["dir_structure", "base_url", "user_prefix"])
        d = yaml.safe_load(open(infofile))
        new = cls.default_scope()
        if prefix := d.get("user_prefix"):
            new.add("_prefix", prefix)

        baseurl = Path(d.get("base_url")) if "base_url" in d else ""
        new.add("_baseurl", str(baseurl), path=Path(infofile))

        for k, v in d.items():
            # FIXME - we are currently skipping subdicts...
            # How to deal with that?
            if k not in special_keys and isinstance(v, str):
                new.add(k, v)
        return new

    @classmethod
    def default_scope(cls) -> "Scope":
        """Returns a new default scope."""
        if "default_scope" not in _cache:
            s = _cache["default_scope"] = cls()
            s.add("@id", "${_prefix}:${_name}")
            s.add("title", "${_name}")
            s.add("releaseDate", "${_ctime}")
            s.add("distribution.downloadURL", "${_pathurl}")
        return _cache["default_scope"].copy()

    def _get_substitutions(self, path: PathType) -> dict:
        """Return substitution pattern for `path`."""
        print()
        p = Path(path)
        base = self.getpath("_baseurl").resolve().parent  # type: ignore
        relpath = p.relative_to(base.parent)
        relroot = p.relative_to(base)
        pathurl = ""
        if "_baseurl" in self:
            r = urlsplit(self["_baseurl"])
            root = Path(unquote(r.path))
            base = self.getpath("_baseurl").resolve().parent  # type: ignore
            # Just quote space - urllib.parse.quote() quotes too much...
            quoted = str(root / relroot).replace(" ", "%20")
            pathurl = urlunsplit((r.scheme, r.netloc, quoted, "", ""))
        d = {
            "_path": relpath,
            "_name": p.name,
            "_ctime": datetime.fromtimestamp(p.stat().st_ctime).isoformat(),
            "_mtime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
            "_pathurl": pathurl,
            "_parent": self.parent.get("@id", "") if self.parent else "",
        }
        for k, v in self.items():
            d[k] = v
        return d

    def document(self, path: PathType) -> dict:
        """Return a dict documenting `path`."""
        subs = self._get_substitutions(path)
        d = {}
        for key in self:
            t = self.gettemplate(key)
            if t and not key.startswith("_"):
                v = t.substitute(subs)
                if sep := self.getoptions(key, {}).get("sep"):
                    v = v.split(sep)
                d[key] = v
        return d


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


# def match(filename: str, patterns: Sequence):
#    """Returns whether `filename` matches any wildcard pattern in `patterns`."""
#    for pattern in patterns:
#        if fnmatch.fnmatchcase(filename, pattern):
#            return True
#    return False
#
#
# def docdir(rootdir: str, scope: Optional[Scope]) -> list:
#    """Recursively documents a directory structure.
#
#    Arguments:
#        rootdir: Root of directory structure to document.
#        scope: Scope
#
#    Returns:
#        List of dicts documenting all datasets in the directory structure.
#    """
#    metadata_pattern = "__METADATA__.*"
#    scope = scope if scope else Scope.default_scope()
#    ignored = [metadata_pattern]  # List of wildcard patterns to ignore
#    doc = []
#
#    try:
#        with os.scandir(rootdir) as entries:
#            for path in Path(rootdir).glob(metadata_pattern):
#                scope = scope.merge(path)
#
#            for entry in entries:
#                if match(entry.name, ignored):
#                    continue
#                if entry.is_file():
#                    doc.append(scope.document(entry.path))
#                elif entry.is_dir():
#                    doc.extend(docdir(entry.path, scope.copy()))
#    except PermissionError:
#        print(f"Permission denied: {rootdir}")
#
#    return doc
