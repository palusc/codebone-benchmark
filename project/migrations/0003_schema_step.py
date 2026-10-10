"""Historical migration 0003; not used by the runtime benchmark."""

REVISION = "0003"


def upgrade(schema):
    schema.append("migration_0003")
    return schema
