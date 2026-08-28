from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("stories", "0003_story_parent_activity"),
    ]

    operations = [
        migrations.AddField(
            model_name="story",
            name="clouds_last_read_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
