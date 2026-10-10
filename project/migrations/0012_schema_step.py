"""Historical migration 0012; not used by the runtime benchmark."""

REVISION = "0012"


def upgrade(schema):
    schema.append("migration_0012")
    return schema
