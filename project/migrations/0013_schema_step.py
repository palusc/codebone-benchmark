"""Historical migration 0013; not used by the runtime benchmark."""

REVISION = "0013"


def upgrade(schema):
    schema.append("migration_0013")
    return schema
