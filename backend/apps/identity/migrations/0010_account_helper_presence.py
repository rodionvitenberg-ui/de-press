from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("identity", "0009_account_is_on_duty"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="helper_seen_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="account",
            name="helper_last_matched_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
