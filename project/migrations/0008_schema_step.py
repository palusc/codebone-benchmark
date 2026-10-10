"""Historical migration 0008; not used by the runtime benchmark."""

REVISION = "0008"


def upgrade(schema):
    schema.append("migration_0008")
    return schema
