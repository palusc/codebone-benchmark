"""Historical migration 0011; not used by the runtime benchmark."""

REVISION = "0011"


def upgrade(schema):
    schema.append("migration_0011")
    return schema
