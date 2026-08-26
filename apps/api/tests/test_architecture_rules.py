"""Executable import-boundary checks for the modular backend skeleton."""

import ast
from dataclasses import dataclass
from pathlib import Path


_MODULE_ROOT = Path(__file__).resolve().parents[1] / "app" / "modules"
_DOMAIN_FORBIDDEN_ROOTS = {
    "anthropic",
    "fastapi",
    "google",
    "linkedin_api",
    "openai",
    "temporalio",
    "tweepy",
}
_WORKFLOW_SIDE_EFFECT_ROOTS = _DOMAIN_FORBIDDEN_ROOTS | {
    "alembic",
    "httpx",
    "redis",
    "requests",
    "sqlalchemy",
}
_CROSS_MODULE_PRIVATE_LAYERS = {"models", "repositories", "repository"}


@dataclass(frozen=True)
class ImportViolation:
    path: Path
    imported: str
    reason: str


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def _violations(module_root: Path) -> list[ImportViolation]:
    violations: list[ImportViolation] = []
    for path in module_root.rglob("*.py"):
        relative = path.relative_to(module_root)
        if not relative.parts:
            continue
        source_module = relative.parts[0]
        is_domain = path.stem == "domain" or "domain" in relative.parts
        is_workflow = (
            path.stem in {"workflow", "workflows"}
            or bool({"workflow", "workflows"}.intersection(relative.parts[:-1]))
        )

        for imported in _imports(path):
            imported_parts = imported.split(".")
            imported_root = imported_parts[0]
            if is_domain and imported_root in _DOMAIN_FORBIDDEN_ROOTS:
                violations.append(
                    ImportViolation(path, imported, "domain depends on infrastructure")
                )
            if is_workflow and imported_root in _WORKFLOW_SIDE_EFFECT_ROOTS:
                violations.append(
                    ImportViolation(
                        path,
                        imported,
                        "workflow performs or imports side-effect infrastructure",
                    )
                )
            if (
                len(imported_parts) >= 4
                and imported_parts[:2] == ["app", "modules"]
                and imported_parts[2] != source_module
                and imported_parts[3] in _CROSS_MODULE_PRIVATE_LAYERS
            ):
                violations.append(
                    ImportViolation(
                        path,
                        imported,
                        "module imports another module's private persistence layer",
                    )
                )
    return violations


def test_backend_module_skeleton_respects_import_boundaries() -> None:
    assert _violations(_MODULE_ROOT) == []


def test_rule_rejects_domain_framework_dependency(tmp_path: Path) -> None:
    domain = tmp_path / "content" / "domain.py"
    domain.parent.mkdir(parents=True)
    domain.write_text("from fastapi import HTTPException\n", encoding="utf-8")

    violations = _violations(tmp_path)

    assert len(violations) == 1
    assert violations[0].reason == "domain depends on infrastructure"


def test_rule_rejects_cross_module_repository_import(tmp_path: Path) -> None:
    service = tmp_path / "publishing" / "service.py"
    service.parent.mkdir(parents=True)
    service.write_text(
        "from app.modules.content.repositories import ContentRepository\n",
        encoding="utf-8",
    )

    violations = _violations(tmp_path)

    assert len(violations) == 1
    assert violations[0].reason == (
        "module imports another module's private persistence layer"
    )


def test_rule_rejects_side_effect_import_in_nested_workflow(tmp_path: Path) -> None:
    workflow_file = tmp_path / "publishing" / "workflows" / "sync.py"
    workflow_file.parent.mkdir(parents=True)
    workflow_file.write_text("from sqlalchemy.orm import Session\n", encoding="utf-8")

    violations = _violations(tmp_path)

    assert len(violations) == 1
    assert violations[0].reason == (
        "workflow performs or imports side-effect infrastructure"
    )
