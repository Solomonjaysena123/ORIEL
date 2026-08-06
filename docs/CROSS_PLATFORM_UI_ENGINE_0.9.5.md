# ORIEL Cross-Platform UI Engine 0.9.5

ORIEL 0.9.5 provides a shared declarative UI model. Applications build one semantic component tree, while renderer implementations translate it for web, tests, and future native platforms.

## Components and nodes

```python
from oriel.ui_engine import Component, Semantics, column, element, text

class Welcome(Component):
    def render(self, context):
        return column(
            text(context.t("welcome", name="ORIEL")),
            element(
                "button",
                "Continue",
                semantics=Semantics(role="button", label="Continue"),
            ),
            gap=16,
        )
```

`Node` values are immutable and support deterministic traversal. Components render nodes using a `UIContext` containing the active platform, display density, theme, and localizer.

## Layout

`Layout` supports flex rows and columns, grids, overlay stacks, gap, padding, margin, width and height, minimum and maximum constraints, alignment, justification, wrapping, growth, and shrinking. Invalid geometry is returned by `validate_tree`.

CSS dimensions accepted by the HTML renderer are restricted to non-negative numeric values and safe units. Arbitrary CSS expressions are rejected.

## State and rendering

```python
from oriel.ui_engine import HTMLRenderer, State, UIEngine

count = State(0)
engine = UIEngine(HTMLRenderer())
unsubscribe = engine.bind(count, lambda context: text(count.value))
count.update(lambda value: value + 1)
unsubscribe()
```

`State` updates and subscription changes are protected for concurrent access. Listeners are called outside the state lock, allowing safe reentrant updates.

The renderer protocol is backend-neutral. Version 0.9.5 includes:

- `MemoryRenderer` for deterministic tests and adapters.
- `HTMLRenderer` as an escaped reference renderer.

Native Android, iOS, Windows, macOS, and Linux renderers are not included in this release.

## Themes and localization

Themes provide inherited color, spacing, typography, radius, and shadow tokens. The HTML reference renderer accepts validated foreground and background color tokens.

`Localizer` supports exact and language-level locale matching, a configured fallback locale, named interpolation, singular/other plural forms, and UTF-8 JSON bundles.

## Accessibility and security

Semantics cover roles, labels, hints, values, enabled/hidden state, live regions, and heading levels. Validation detects missing interactive labels, missing image alternatives, invalid semantic values, duplicate keys, and invalid layouts.

The HTML renderer:

- escapes text and attribute content;
- rejects control characters and unsupported URL schemes such as `javascript:` and `data:`;
- restricts CSS sizes and theme colors;
- renders semantic heading levels and ARIA attributes.

The HTML renderer produces fragments and is not a browser sandbox. Applications must continue to use the v0.9.3 security headers and normal Content Security Policy when serving UI output.

## CLI

```bash
oriel ui new example
```

The command creates an ORIEL source entry point, localization assets, tests directory, package manifest, and README.
