"""Static Alembic graph checks that fail before a database is touched."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


_API_ROOT = Path(__file__).resolve().parents[1]


def _scripts() -> ScriptDirectory:
    config = Config(str(_API_ROOT / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(_API_ROOT / "app" / "db" / "migrations"),
    )
    return ScriptDirectory.from_config(config)


def test_migration_graph_has_exactly_one_coordinated_head() -> None:
    scripts = _scripts()

    assert scripts.get_heads() == ["011_idempotency_reconnect"]


def test_every_migration_has_upgrade_and_downgrade_entry_points() -> None:
    revisions = list(_scripts().walk_revisions(base="base", head="heads"))

    assert revisions
    for revision in revisions:
        assert callable(getattr(revision.module, "upgrade", None)), revision.revision
        assert callable(getattr(revision.module, "downgrade", None)), revision.revision
