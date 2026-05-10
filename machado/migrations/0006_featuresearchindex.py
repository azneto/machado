import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("machado", "0005_add_db_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="Feature",
            fields=[
                ("feature_id", models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                "db_table": "feature",
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="FeatureSearchIndex",
            fields=[
                (
                    "feature",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="search_index",
                        serialize=False,
                        to="machado.feature",
                    ),
                ),
                (
                    "search_vector",
                    django.contrib.postgres.search.SearchVectorField(null=True),
                ),
                ("autocomplete_text", models.TextField(default="")),
                ("organism", models.CharField(default="", max_length=512)),
                ("so_term", models.CharField(default="", max_length=128)),
                ("uniquename", models.CharField(default="", max_length=1024)),
                ("name", models.CharField(blank=True, max_length=1024, null=True)),
                ("display", models.CharField(blank=True, max_length=4096, null=True)),
                ("analyses", models.JSONField(default=list)),
                ("doi", models.JSONField(default=list)),
                ("biomaterial", models.JSONField(default=list)),
                ("treatment", models.JSONField(default=list)),
                ("orthology", models.BooleanField(default=False)),
                (
                    "orthologous_group",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("coexpression", models.BooleanField(default=False)),
                (
                    "coexpression_group",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("relationships", models.JSONField(default=list)),
                ("orthologs_coexpression", models.JSONField(default=list)),
            ],
            options={
                "db_table": "machado_featuresearchindex",
                "managed": True,
                "indexes": [
                    django.contrib.postgres.indexes.GinIndex(
                        fields=["search_vector"], name="fsi_search_gin"
                    ),
                    models.Index(fields=["organism"], name="fsi_organism_idx"),
                    models.Index(fields=["so_term"], name="fsi_so_term_idx"),
                    models.Index(fields=["uniquename"], name="fsi_uniquename_idx"),
                    models.Index(
                        fields=["orthologous_group"], name="fsi_ortho_grp_idx"
                    ),
                    models.Index(
                        fields=["coexpression_group"], name="fsi_coexp_grp_idx"
                    ),
                ],
            },
        ),
    ]
