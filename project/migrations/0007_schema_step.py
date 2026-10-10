"""Historical migration 0007; not used by the runtime benchmark."""

REVISION = "0007"


def upgrade(schema):
    schema.append("migration_0007")
    return schema
