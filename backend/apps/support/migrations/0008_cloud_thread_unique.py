from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("support", "0007_cloud_thread_unique"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="supportcloud",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("from_account__isnull", False),
                    ("thread_root__isnull", False),
                )
                & ~models.Q(("status", "rejected")),
                fields=("thread_root", "from_account"),
                name="unique_cloud_per_account_thread",
            ),
        ),
        migrations.AddConstraint(
            model_name="supportcloud",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("from_session__isnull", False),
                    ("thread_root__isnull", False),
                )
                & ~models.Q(("status", "rejected")),
                fields=("thread_root", "from_session"),
                name="unique_cloud_per_session_thread",
            ),
        ),
        migrations.AddIndex(
            model_name="supportcloud",
            index=models.Index(
                fields=["thread_root", "status", "-created_at"],
                name="support_sup_thread__idx",
            ),
        ),
    ]
