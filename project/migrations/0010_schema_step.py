"""Historical migration 0010; not used by the runtime benchmark."""

REVISION = "0010"


def upgrade(schema):
    schema.append("migration_0010")
    return schema
