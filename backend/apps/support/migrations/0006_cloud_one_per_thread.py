from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("stories", "0005_story_voice"),
        ("support", "0005_one_cloud_per_sender_story"),
    ]

    operations = [
        migrations.AddField(
            model_name="supportcloud",
            name="thread_root",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="thread_support_clouds",
                to="stories.story",
            ),
        ),
    ]
