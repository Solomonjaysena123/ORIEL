from __future__ import annotations

"""ORIEL 0.9.5 cross-platform UI engine.

The engine is deliberately backend-neutral. Applications construct a semantic
component tree once; renderers translate that tree for web, desktop, mobile,
terminal, test, or future native targets.
"""

from dataclasses import dataclass, field, fields, replace
from html import escape
from pathlib import Path
from typing import Any, Callable, Generic, Iterable, Mapping, Protocol, TypeVar
import json
import math
import re
import threading
from urllib.parse import urlsplit

T = TypeVar("T")
StateListener = Callable[[Any], None]


@dataclass(frozen=True, slots=True)
class Semantics:
    role: str | None = None
    label: str | None = None
    hint: str | None = None
    value: str | None = None
    enabled: bool = True
    hidden: bool = False
    live_region: str | None = None
    heading_level: int | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.heading_level is not None and not 1 <= self.heading_level <= 6:
            issues.append("heading_level must be between 1 and 6")
        if self.live_region not in (None, "off", "polite", "assertive"):
            issues.append("live_region must be off, polite, or assertive")
        if self.role in {"button", "link", "textbox", "checkbox", "image"} and not self.label:
            issues.append(f"accessible label required for role '{self.role}'")
        return issues


@dataclass(frozen=True, slots=True)
class EdgeInsets:
    top: float = 0
    right: float = 0
    bottom: float = 0
    left: float = 0

    @classmethod
    def all(cls, value: float) -> "EdgeInsets":
        return cls(value, value, value, value)

    @classmethod
    def symmetric(cls, *, horizontal: float = 0, vertical: float = 0) -> "EdgeInsets":
        return cls(vertical, horizontal, vertical, horizontal)

    def validate(self) -> list[str]:
        values=(self.top,self.right,self.bottom,self.left)
        return ["insets must be finite and non-negative"] if any(
            not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 for value in values
        ) else []


@dataclass(frozen=True, slots=True)
class Layout:
    display: str = "flex"
    direction: str = "column"
    gap: float = 0
    padding: EdgeInsets = field(default_factory=EdgeInsets)
    margin: EdgeInsets = field(default_factory=EdgeInsets)
    width: float | str | None = None
    height: float | str | None = None
    min_width: float | None = None
    min_height: float | None = None
    max_width: float | None = None
    max_height: float | None = None
    align: str = "stretch"
    justify: str = "start"
    wrap: bool = False
    grow: float = 0
    shrink: float = 1
    grid_columns: int | None = None

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.display not in {"flex", "grid", "stack", "none"}:
            issues.append(f"unsupported display mode: {self.display}")
        if self.direction not in {"row", "column"}:
            issues.append("direction must be row or column")
        if not isinstance(self.gap,(int,float)) or not math.isfinite(self.gap) or self.gap<0:
            issues.append("gap must be finite and non-negative")
        if self.grid_columns is not None and self.grid_columns < 1:
            issues.append("grid_columns must be positive")
        if self.align not in {"start","end","center","stretch","baseline"}:
            issues.append("unsupported alignment")
        if self.justify not in {"start","end","center","space-between","space-around","space-evenly"}:
            issues.append("unsupported justification")
        if any(not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 for value in (self.grow,self.shrink)):
            issues.append("grow and shrink must be finite and non-negative")
        issues.extend(self.padding.validate())
        issues.extend(self.margin.validate())
        numeric_constraints=(self.min_width,self.min_height,self.max_width,self.max_height)
        if any(value is not None and (not isinstance(value,(int,float)) or not math.isfinite(value) or value<0) for value in numeric_constraints):
            issues.append("layout constraints must be finite and non-negative")
        if self.min_width is not None and self.max_width is not None and self.min_width>self.max_width:
            issues.append("min_width cannot exceed max_width")
        if self.min_height is not None and self.max_height is not None and self.min_height>self.max_height:
            issues.append("min_height cannot exceed max_height")
        return issues


@dataclass(frozen=True, slots=True)
class Theme:
    name: str
    colors: Mapping[str, str] = field(default_factory=dict)
    spacing: Mapping[str, float] = field(default_factory=dict)
    typography: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    radii: Mapping[str, float] = field(default_factory=dict)
    shadows: Mapping[str, str] = field(default_factory=dict)
    parent: "Theme | None" = None

    def token(self, path: str, default: Any = None) -> Any:
        group, _, key = path.partition(".")
        source = getattr(self, group, None)
        if isinstance(source, Mapping) and key in source:
            return source[key]
        return self.parent.token(path, default) if self.parent else default

    def extend(self, name: str, **overrides: Mapping[str, Any]) -> "Theme":
        values: dict[str, Any] = {"name": name, "parent": self}
        for group in ("colors", "spacing", "typography", "radii", "shadows"):
            values[group] = overrides.get(group, {})
        return Theme(**values)


DEFAULT_THEME = Theme(
    "oriel-light",
    colors={"primary": "#2563EB", "surface": "#FFFFFF", "text": "#111827", "danger": "#DC2626"},
    spacing={"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32},
    typography={"body": {"size": 16, "weight": 400}, "heading": {"size": 28, "weight": 700}},
    radii={"sm": 4, "md": 8, "lg": 16},
)


class Localizer:
    _PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")

    def __init__(self, bundles: Mapping[str, Mapping[str, Any]], locale: str, fallback_locale: str = "en") -> None:
        self.bundles = {key: dict(value) for key, value in bundles.items()}
        self.locale = locale
        self.fallback_locale = fallback_locale

    def set_locale(self, locale: str) -> None:
        self.locale = locale

    def _bundle_chain(self) -> Iterable[Mapping[str, Any]]:
        seen: set[str] = set()
        for locale in (self.locale, self.locale.split("-")[0], self.fallback_locale):
            if locale not in seen and locale in self.bundles:
                seen.add(locale)
                yield self.bundles[locale]

    def translate(self, key: str, *, count: int | float | None = None, **values: Any) -> str:
        raw: Any = None
        for bundle in self._bundle_chain():
            if key in bundle:
                raw = bundle[key]
                break
        if raw is None:
            return key
        if isinstance(raw, Mapping):
            form = "one" if count == 1 else "other"
            raw = raw.get(form, raw.get("other", key))
            values.setdefault("count", count)
        text = str(raw)
        return self._PLACEHOLDER.sub(lambda match: str(values.get(match.group(1), match.group(0))), text)

    @classmethod
    def from_json(cls, path: Path, locale: str, fallback_locale: str = "en") -> "Localizer":
        return cls(json.loads(path.read_text(encoding="utf-8")), locale, fallback_locale)


class State(Generic[T]):
    def __init__(self, value: T) -> None:
        self._value = value
        self._listeners: list[StateListener] = []
        self._lock = threading.RLock()

    @property
    def value(self) -> T:
        with self._lock:
            return self._value

    def set(self, value: T) -> None:
        with self._lock:
            if value == self._value:
                return
            self._value = value
            listeners=tuple(self._listeners)
        for listener in listeners:
            listener(value)

    def update(self, operation: Callable[[T], T]) -> None:
        with self._lock:
            value=operation(self._value)
            if value==self._value: return
            self._value=value
            listeners=tuple(self._listeners)
        for listener in listeners:
            listener(value)

    def subscribe(self, listener: StateListener, *, emit_current: bool = False) -> Callable[[], None]:
        if not callable(listener): raise TypeError("state listener must be callable")
        with self._lock:
            self._listeners.append(listener)
            current=self._value
        if emit_current:
            listener(current)

        def unsubscribe() -> None:
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)

        return unsubscribe


@dataclass(frozen=True, slots=True)
class Node:
    kind: str
    props: Mapping[str, Any] = field(default_factory=dict)
    children: tuple["Node", ...] = ()
    key: str | None = None
    layout: Layout | None = None
    semantics: Semantics | None = None

    def with_children(self, *children: "Node") -> "Node":
        return replace(self, children=tuple(children))

    def walk(self) -> Iterable["Node"]:
        yield self
        for child in self.children:
            yield from child.walk()


def text(value: Any, **props: Any) -> Node:
    return Node("text", {"value": str(value), **props})


def element(
    kind: str,
    *children: Node | str,
    key: str | None = None,
    layout: Layout | None = None,
    semantics: Semantics | None = None,
    **props: Any,
) -> Node:
    normalized = tuple(child if isinstance(child, Node) else text(child) for child in children)
    return Node(kind, props, normalized, key, layout, semantics)


def row(*children: Node | str, gap: float = 0, **props: Any) -> Node:
    return element("container", *children, layout=Layout(direction="row", gap=gap), **props)


def column(*children: Node | str, gap: float = 0, **props: Any) -> Node:
    return element("container", *children, layout=Layout(direction="column", gap=gap), **props)


class Component:
    def render(self, context: "UIContext") -> Node:
        raise NotImplementedError


@dataclass(slots=True)
class UIContext:
    theme: Theme = DEFAULT_THEME
    localizer: Localizer = field(default_factory=lambda: Localizer({"en": {}}, "en"))
    platform: str = "generic"
    density: float = 1.0

    def t(self, key: str, **values: Any) -> str:
        return self.localizer.translate(key, **values)


@dataclass(frozen=True, slots=True)
class RenderTree:
    platform: str
    root: Any
    diagnostics: tuple[str, ...] = ()


class Renderer(Protocol):
    platform: str

    def render(self, node: Node, context: UIContext) -> RenderTree: ...


class MemoryRenderer:
    platform = "memory"

    def render(self, node: Node, context: UIContext) -> RenderTree:
        diagnostics = tuple(validate_tree(node))

        def encode(current: Node) -> dict[str, Any]:
            return {
                "kind": current.kind,
                "key": current.key,
                "props": dict(current.props),
                "layout": None if current.layout is None else {
                    item.name: getattr(current.layout, item.name) for item in fields(current.layout)
                },
                "semantics": None if current.semantics is None else {
                    item.name: getattr(current.semantics, item.name) for item in fields(current.semantics)
                },
                "children": [encode(child) for child in current.children],
            }

        return RenderTree(self.platform, encode(node), diagnostics)


class HTMLRenderer:
    platform = "web"
    _TAGS = {"container": "div", "text": "span", "button": "button", "image": "img", "input": "input", "link": "a", "heading": "h2"}
    _CSS_SIZE = re.compile(r"(?:0|(?:\d+(?:\.\d+)?)(?:px|%|rem|em|vw|vh))\Z")
    _COLOR = re.compile(r"(?:#[0-9A-Fa-f]{3,8}|[A-Za-z]+)\Z")

    @classmethod
    def _size(cls,value:float|str)->str:
        if isinstance(value,(int,float)):
            if not math.isfinite(value) or value<0: raise ValueError("CSS size must be finite and non-negative")
            return f"{value}px"
        if value in {"auto","min-content","max-content","fit-content"} or cls._CSS_SIZE.fullmatch(value):
            return value
        raise ValueError(f"unsafe or unsupported CSS size: {value}")

    @staticmethod
    def _url(value:Any)->str:
        rendered=str(value)
        if any(character in rendered for character in "\r\n\x00"): raise ValueError("invalid URL")
        parsed=urlsplit(rendered)
        if parsed.scheme.lower() not in {"","http","https","mailto","tel"}:
            raise ValueError(f"unsupported URL scheme: {parsed.scheme}")
        return rendered

    def render(self, node: Node, context: UIContext) -> RenderTree:
        diagnostics = tuple(validate_tree(node))

        def style(current: Node,stack_child:bool=False) -> str:
            layout = current.layout
            rules:list[str]=[]
            if stack_child: rules.append("grid-area:1/1")
            if layout is not None:
                display={"stack":"grid"}.get(layout.display,layout.display)
                rules.append(f"display:{display}")
                if layout.display == "flex":
                    rules += [f"flex-direction:{layout.direction}", f"gap:{layout.gap}px", f"align-items:{layout.align}", f"justify-content:{layout.justify}"]
                if layout.display == "grid" and layout.grid_columns:
                    rules.append(f"grid-template-columns:repeat({layout.grid_columns},minmax(0,1fr))")
                if layout.width is not None: rules.append(f"width:{self._size(layout.width)}")
                if layout.height is not None: rules.append(f"height:{self._size(layout.height)}")
                for css_name,value in (("min-width",layout.min_width),("min-height",layout.min_height),("max-width",layout.max_width),("max-height",layout.max_height)):
                    if value is not None: rules.append(f"{css_name}:{self._size(value)}")
                rules.extend((f"flex-grow:{layout.grow}",f"flex-shrink:{layout.shrink}"))
                if layout.wrap: rules.append("flex-wrap:wrap")
                p = layout.padding; m = layout.margin
                rules += [f"padding:{p.top}px {p.right}px {p.bottom}px {p.left}px", f"margin:{m.top}px {m.right}px {m.bottom}px {m.left}px"]
            for prop,token_group in (("foreground_token","colors"),("background_token","colors")):
                if prop in current.props:
                    token=context.theme.token(f"{token_group}.{current.props[prop]}")
                    if not isinstance(token,str) or not self._COLOR.fullmatch(token): raise ValueError(f"invalid theme color token: {current.props[prop]}")
                    rules.append(f"{'color' if prop=='foreground_token' else 'background-color'}:{token}")
            return ";".join(rules)

        def encode(current: Node,stack_child:bool=False) -> str:
            if current.kind == "text":
                value=escape(str(current.props.get("value","")))
                inline_style=style(current,stack_child)
                return f'<span style="{escape(inline_style)}">{value}</span>' if inline_style else value
            tag = self._TAGS.get(current.kind, "div")
            if current.kind=="heading" and current.semantics and current.semantics.heading_level:
                tag=f"h{current.semantics.heading_level}"
            attrs: list[str] = []
            semantics = current.semantics
            if semantics:
                if semantics.role: attrs.append(f'role="{escape(semantics.role)}"')
                if semantics.label: attrs.append(f'aria-label="{escape(semantics.label)}"')
                if semantics.hint: attrs.append(f'aria-description="{escape(semantics.hint)}"')
                if semantics.hidden: attrs.append('aria-hidden="true"')
                if semantics.live_region: attrs.append(f'aria-live="{escape(semantics.live_region)}"')
                if not semantics.enabled: attrs.append("disabled")
            inline_style = style(current,stack_child)
            if inline_style: attrs.append(f'style="{escape(inline_style)}"')
            for name in ("id", "class", "href", "src", "alt", "type", "name", "value", "placeholder"):
                if name in current.props:
                    value=self._url(current.props[name]) if name in {"href","src"} else str(current.props[name])
                    attrs.append(f'{name}="{escape(value)}"')
            is_stack=current.layout is not None and current.layout.display=="stack"
            content = "".join(encode(child,is_stack) for child in current.children)
            if tag in {"img", "input"}:
                return f"<{tag}{(' ' + ' '.join(attrs)) if attrs else ''}>"
            return f"<{tag}{(' ' + ' '.join(attrs)) if attrs else ''}>{content}</{tag}>"

        return RenderTree(self.platform, encode(node), diagnostics)


class UIEngine:
    def __init__(self, renderer: Renderer, context: UIContext | None = None) -> None:
        self.renderer = renderer
        self.context = context or UIContext(platform=renderer.platform)
        self._last_tree: RenderTree | None = None

    def mount(self, root: Component | Node) -> RenderTree:
        node = root.render(self.context) if isinstance(root, Component) else root
        self._last_tree = self.renderer.render(node, self.context)
        return self._last_tree

    def bind(self, state: State[Any], root: Component | Callable[[UIContext], Node]) -> Callable[[], None]:
        def rerender(_: Any) -> None:
            node = root.render(self.context) if isinstance(root, Component) else root(self.context)
            self._last_tree = self.renderer.render(node, self.context)
        rerender(state.value)
        return state.subscribe(rerender)

    @property
    def last_tree(self) -> RenderTree | None:
        return self._last_tree


def validate_tree(root: Node) -> list[str]:
    issues: list[str] = []
    keys: set[str] = set()
    for node in root.walk():
        if node.key:
            if node.key in keys:
                issues.append(f"duplicate key: {node.key}")
            keys.add(node.key)
        if node.layout:
            issues.extend(f"{node.kind}: {issue}" for issue in node.layout.validate())
        if node.semantics:
            issues.extend(f"{node.kind}: {issue}" for issue in node.semantics.validate())
        if node.kind == "image" and not (node.props.get("alt") or (node.semantics and node.semantics.label)):
            issues.append("image: alternative text or semantics label required")
    return issues


def create_ui_project(name: str, base: Path = Path.cwd()) -> Path:
    clean = name.strip()
    if not clean or any(char in clean for char in '\\/:*?"<>|'):
        raise ValueError("Project name contains invalid characters")
    project = base / clean
    if project.exists():
        raise FileExistsError(f"Project already exists: {project}")
    (project / "src").mkdir(parents=True)
    (project / "assets" / "i18n").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "src" / "main.orl").write_text(
        'use oriel.ui\n\ncomponent App {\n    state count: Int = 0\n\n    render {\n        Column(gap: 16) {\n            Heading("ORIEL Cross-Platform UI")\n            Text("Count: {count}")\n            Button("Increment", onPress: { count = count + 1 })\n        }\n    }\n}\n',
        encoding="utf-8",
    )
    (project / "assets" / "i18n" / "en.json").write_text('{"app.title":"ORIEL Cross-Platform UI"}\n', encoding="utf-8")
    (project / "oriel.toml").write_text(
        f'[project]\nname = "{clean}"\nversion = "0.1.0"\nentry = "src/main.orl"\n\n[dependencies]\noriel.ui = "0.9.5"\n',
        encoding="utf-8",
    )
    (project / "README.md").write_text(
        f"# {clean}\n\nCreated with ORIEL 0.9.5 Cross-Platform UI Engine.\n",
        encoding="utf-8",
    )
    return project
