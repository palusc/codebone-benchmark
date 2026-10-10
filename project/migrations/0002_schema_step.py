"""Historical migration 0002; not used by the runtime benchmark."""

REVISION = "0002"


def upgrade(schema):
    schema.append("migration_0002")
    return schema
