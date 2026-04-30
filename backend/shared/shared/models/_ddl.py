"""Raw DDL fragments that don't fit cleanly into SQLAlchemy table definitions.

These are imported by alembic migrations and emitted via ``op.execute``.
Keeping them here (rather than inlined in versions/*.py) means migrations
stay readable and the SQL is reviewable in one place.
"""

from __future__ import annotations

# plpgsql function attached as a BEFORE UPDATE row-level trigger to every
# table that has an ``updated_at`` column. Sets ``NEW.updated_at`` to ``now()``
# so application code never has to remember.
SET_UPDATED_AT_FUNCTION = """\
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;
"""

DROP_SET_UPDATED_AT_FUNCTION = "DROP FUNCTION IF EXISTS public.set_updated_at();"


def trigger_set_updated_at_sql(schema: str, table: str) -> str:
    """Return the SQL that installs the BEFORE UPDATE trigger on a table."""
    trigger_name = f"trg_{table}_set_updated_at"
    return (
        f"CREATE TRIGGER {trigger_name} "
        f"BEFORE UPDATE ON {schema}.{table} "
        f"FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();"
    )


def drop_trigger_set_updated_at_sql(schema: str, table: str) -> str:
    trigger_name = f"trg_{table}_set_updated_at"
    return f"DROP TRIGGER IF EXISTS {trigger_name} ON {schema}.{table};"


# CREATE TYPE statements for the shared enums. Emitted from the baseline
# migration before any CREATE TABLE that references them.
CREATE_ENUM_TYPES = [
    "CREATE TYPE sex AS ENUM ('男', '女');",
    "CREATE TYPE patient_source AS ENUM ('main', 'external', 'nbs');",
    "CREATE TYPE link_kind AS ENUM ('same_person', 'probable', 'manual');",
]

DROP_ENUM_TYPES = [
    "DROP TYPE IF EXISTS link_kind;",
    "DROP TYPE IF EXISTS patient_source;",
    "DROP TYPE IF EXISTS sex;",
]

__all__ = [
    "SET_UPDATED_AT_FUNCTION",
    "DROP_SET_UPDATED_AT_FUNCTION",
    "trigger_set_updated_at_sql",
    "drop_trigger_set_updated_at_sql",
    "CREATE_ENUM_TYPES",
    "DROP_ENUM_TYPES",
]
