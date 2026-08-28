from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0002_emaildigest"),
    ]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("dialogue_request", "Dialogue request"),
                    ("support_cloud", "Support cloud"),
                    ("cloud_approved", "Support cloud approved"),
                    ("dialogue_opened", "Dialogue opened"),
                    ("outreach_intro", "Author outreach intro"),
                    ("message", "New chat message"),
                    ("dialogue_deleted", "Dialogue deleted"),
                ],
                db_index=True,
                max_length=32,
            ),
        ),
    ]
