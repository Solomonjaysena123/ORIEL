import json
import threading
from pathlib import Path

import pytest

from oriel.cli import build_parser
from oriel.ui_engine import (
    DEFAULT_THEME,
    Component,
    EdgeInsets,
    HTMLRenderer,
    Layout,
    Localizer,
    MemoryRenderer,
    Semantics,
    State,
    Theme,
    UIContext,
    UIEngine,
    column,
    create_ui_project,
    element,
    row,
    text,
    validate_tree,
)


def test_declarative_tree_walk_and_backend_neutral_memory_rendering():
    tree=column(text("Title"),row("A","B",gap=8),gap=16)
    assert [node.kind for node in tree.walk()]==["container","text","container","text","text"]
    rendered=MemoryRenderer().render(tree,UIContext(platform="desktop"))
    assert rendered.platform=="memory"
    assert rendered.root["layout"]["direction"]=="column"
    assert rendered.root["children"][1]["children"][0]["props"]["value"]=="A"


def test_state_change_notifications_unsubscribe_and_thread_safety():
    state=State(0)
    values=[]
    unsubscribe=state.subscribe(values.append,emit_current=True)
    state.set(0)
    threads=[threading.Thread(target=lambda:state.update(lambda value:value+1)) for _ in range(20)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    unsubscribe()
    state.set(30)
    assert state.value==30
    assert values[0]==0
    assert values[-1]==20
    assert len(values)==21
    with pytest.raises(TypeError,match="callable"):
        state.subscribe(None)


def test_engine_binding_mount_and_unsubscribe():
    state=State(0)
    engine=UIEngine(HTMLRenderer())
    stop=engine.bind(state,lambda _:element("button",text(state.value),semantics=Semantics(role="button",label="Count")))
    assert ">0<" in engine.last_tree.root
    state.set(4)
    assert ">4<" in engine.last_tree.root
    stop()
    state.set(5)
    assert ">4<" in engine.last_tree.root

    class Greeting(Component):
        def render(self,context):
            return element("heading",context.t("title"),semantics=Semantics(heading_level=1))

    context=UIContext(localizer=Localizer({"en":{"title":"ORIEL UI"}},"en"))
    assert "<h1" in UIEngine(HTMLRenderer(),context).mount(Greeting()).root


def test_complete_layout_rendering_and_stack_behavior():
    layout=Layout(
        direction="row",gap=12,padding=EdgeInsets.all(8),margin=EdgeInsets.symmetric(horizontal=4),
        width="100%",height=80,min_width=20,max_width=500,align="center",justify="space-between",
        wrap=True,grow=1,shrink=0,
    )
    html=HTMLRenderer().render(element("container","Hello",layout=layout),UIContext()).root
    for expected in (
        "flex-direction:row","gap:12px","padding:8px 8px 8px 8px","margin:0px 4px 0px 4px",
        "width:100%","height:80px","min-width:20px","max-width:500px","flex-wrap:wrap",
        "flex-grow:1","flex-shrink:0","align-items:center","justify-content:space-between",
    ):
        assert expected in html

    stacked=HTMLRenderer().render(
        element("container","back","front",layout=Layout(display="stack")),UIContext()
    ).root
    assert "display:grid" in stacked
    assert stacked.count("grid-area:1/1")==2


def test_layout_validation_rejects_invalid_geometry():
    issues=Layout(
        gap=float("nan"),padding=EdgeInsets.all(-1),align="sideways",justify="random",
        min_width=20,max_width=10,grow=-1,
    ).validate()
    assert any("gap" in issue for issue in issues)
    assert any("insets" in issue for issue in issues)
    assert any("alignment" in issue for issue in issues)
    assert any("justification" in issue for issue in issues)
    assert any("min_width" in issue for issue in issues)
    assert any("grow" in issue for issue in issues)
    with pytest.raises(ValueError,match="CSS size"):
        HTMLRenderer().render(element("container",layout=Layout(width="1px;color:red")),UIContext())


def test_theme_inheritance_and_safe_html_theme_tokens():
    dark=DEFAULT_THEME.extend("dark",colors={"surface":"#000000"})
    node=element("container","content",foreground_token="primary",background_token="surface")
    html=HTMLRenderer().render(node,UIContext(theme=dark)).root
    assert "color:#2563EB" in html
    assert "background-color:#000000" in html
    assert dark.token("spacing.md")==16
    unsafe=Theme("unsafe",colors={"bad":"red;background:url(x)"})
    with pytest.raises(ValueError,match="theme color"):
        HTMLRenderer().render(element("container",background_token="bad"),UIContext(theme=unsafe))


def test_localization_fallback_interpolation_pluralization_and_json(tmp_path:Path):
    bundles={
        "en":{"welcome":"Welcome {name}","items":{"one":"{count} item","other":"{count} items"}},
        "si":{"welcome":"ආයුබෝවන් {name}"},
    }
    localizer=Localizer(bundles,"si-LK")
    assert localizer.translate("welcome",name="ORIEL")=="ආයුබෝවන් ORIEL"
    assert localizer.translate("items",count=1)=="1 item"
    assert localizer.translate("items",count=2)=="2 items"
    assert localizer.translate("missing")=="missing"
    bundle=tmp_path/"messages.json"
    bundle.write_text(json.dumps(bundles,ensure_ascii=False),encoding="utf-8")
    assert Localizer.from_json(bundle,"si").translate("welcome",name="UI")=="ආයුබෝවන් UI"


def test_accessibility_semantics_heading_levels_and_tree_diagnostics():
    bad=column(
        element("button","Go",semantics=Semantics(role="button")),
        element("image",src="photo.png"),
        element("text",key="same",value="A"),
        element("text",key="same",value="B"),
    )
    diagnostics=" ".join(validate_tree(bad))
    assert "accessible label required" in diagnostics
    assert "alternative text" in diagnostics
    assert "duplicate key: same" in diagnostics
    good=element(
        "heading","Accessible",semantics=Semantics(role="heading",label="Accessible",heading_level=3)
    )
    assert validate_tree(good)==[]
    assert HTMLRenderer().render(good,UIContext()).root.startswith("<h3")


def test_html_escaping_and_unsafe_url_schemes():
    renderer=HTMLRenderer()
    html=renderer.render(
        element("link","<open>",href="https://example.com/?a=1&b=2",semantics=Semantics(role="link",label='"Open"')),
        UIContext(),
    ).root
    assert "&lt;open&gt;" in html
    assert "&amp;" in html
    assert "&quot;Open&quot;" in html
    with pytest.raises(ValueError,match="scheme"):
        renderer.render(element("link","bad",href="javascript:alert(1)"),UIContext())
    with pytest.raises(ValueError,match="scheme"):
        renderer.render(element("image",src="data:image/svg+xml,bad",alt="bad"),UIContext())


def test_project_scaffold_and_cli_contract(tmp_path:Path):
    project=create_ui_project("sample-ui",tmp_path)
    assert (project/"src"/"main.orl").exists()
    assert (project/"assets"/"i18n"/"en.json").exists()
    manifest=(project/"oriel.toml").read_text(encoding="utf-8")
    assert 'oriel.ui = "0.9.5"' in manifest
    args=build_parser().parse_args(["ui","new","another","--path",str(tmp_path)])
    assert args.command=="ui"
    assert args.ui_command=="new"
    assert args.name=="another"
    with pytest.raises(ValueError,match="invalid"):
        create_ui_project("../bad",tmp_path)
    with pytest.raises(FileExistsError):
        create_ui_project("sample-ui",tmp_path)
