"""Historical migration 0004; not used by the runtime benchmark."""

REVISION = "0004"


def upgrade(schema):
    schema.append("migration_0004")
    return schema
