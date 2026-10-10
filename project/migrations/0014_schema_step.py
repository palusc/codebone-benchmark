"""Historical migration 0014; not used by the runtime benchmark."""

REVISION = "0014"


def upgrade(schema):
    schema.append("migration_0014")
    return schema
