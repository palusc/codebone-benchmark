"""Historical migration 0009; not used by the runtime benchmark."""

REVISION = "0009"


def upgrade(schema):
    schema.append("migration_0009")
    return schema
