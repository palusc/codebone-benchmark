"""Historical migration 0001; not used by the runtime benchmark."""

REVISION = "0001"


def upgrade(schema):
    schema.append("migration_0001")
    return schema
