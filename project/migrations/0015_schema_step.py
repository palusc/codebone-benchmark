"""Historical migration 0015; not used by the runtime benchmark."""

REVISION = "0015"


def upgrade(schema):
    schema.append("migration_0015")
    return schema
