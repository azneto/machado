"""Create database from chado default_schema.sql."""
import os

from django.db import connection, migrations


def load_data_from_sql(apps, schema_editor):
    """Load data from sql."""
    file_path = os.path.join(os.path.dirname(__file__),
                             '../schemas/1.31/default_schema.sql')
    sql_statement = open(file_path).read()
    with connection.cursor() as c:
        c.execute(sql_statement)


class Migration(migrations.Migration):
    """Migration."""

    operations = [
        migrations.RunPython(load_data_from_sql),
    ]