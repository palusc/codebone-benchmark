"""Historical migration 0006; not used by the runtime benchmark."""

REVISION = "0006"


def upgrade(schema):
    schema.append("migration_0006")
    return schema
