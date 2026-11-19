"""Publish declarative UI through the standard A2UI catalog."""

import json
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from ag_ui_a2ui_toolkit import BASIC_CATALOG_ID, create_surface, update_components, update_data_model
from ag_ui_a2ui_toolkit.validate import validate_a2ui_components
from jsonschema import Draft202012Validator
from langchain_core.tools import tool
from referencing import Registry, Resource

CATALOG_ID = "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"


@lru_cache
def _catalog() -> tuple[dict, Registry]:
    directory = Path(__file__).with_name("a2ui_schemas")
    catalog, common = (
        json.loads((directory / filename).read_text(encoding="utf-8"))
        for filename in ("catalog.json", "common_types.json")
    )
    return catalog, Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in (catalog, common)
    )


@tool(response_format="content_and_artifact")
def publish_a2ui_surface(
    components: list[dict[str, object]],
    data: dict[str, object] | None = None,
) -> tuple[str, dict | None]:
    """Render a visual response using only the standard A2UI v0.9 Basic Catalog.

    Use when the user asks for a visual presentation. Pass a flat array with a
    root component whose id is "root". Each item has an id and a case-sensitive
    component name. Containers reference child IDs, not nested component objects.
    For example: Card uses child: "tabs"; Tabs uses tabs: [{"title": "Summary",
    "child": "summary"}]; Text uses text: "Summary content". Column uses
    children: ["summary", "details"]. Use only information from the conversation.
    Do not emit JSON in your answer after calling this tool. Buttons that send
    actions to the agent are not supported; use local navigation such as tabs.
    """
    if not 1 <= len(components) <= 100:
        return "Provide between 1 and 100 components.", None
    if len(json.dumps([components, data], ensure_ascii=False).encode()) > 128_000:
        return "The surface is too large. Shorten the visual content.", None
    catalog, registry = _catalog()
    for index, component in enumerate(components):
        name = component.get("component")
        if not isinstance(name, str) or name not in catalog["components"]:
            return f"Component {index} must name a component from the Basic Catalog.", None
        ref = f"{CATALOG_ID}#/components/{name}"
        error = next(Draft202012Validator({"$ref": ref}, registry=registry).iter_errors(component), None)
        if error is not None:
            return f"Invalid Basic Catalog component {index} ({name}): {error.message}", None
    result = validate_a2ui_components(components=components, data=data, catalog=catalog)
    if not result["valid"]:
        return f"Invalid A2UI component tree: {result['errors']}", None
    if not any(component.get("id") == "root" for component in components):
        return 'The surface requires a component with id "root".', None
    surface_id = uuid4().hex
    messages = [create_surface(surface_id, BASIC_CATALOG_ID)]
    if data is not None:
        messages.append(update_data_model(surface_id, data))
    messages.append(update_components(surface_id, components))
    return "A2UI surface published. Respond briefly without repeating the JSON.", {
        "a2ui": messages,
    }
