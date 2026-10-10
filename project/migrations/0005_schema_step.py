"""Historical migration 0005; not used by the runtime benchmark."""

REVISION = "0005"


def upgrade(schema):
    schema.append("migration_0005")
    return schema
