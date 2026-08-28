from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("stories", "0002_story_topic"),
    ]

    operations = [
        migrations.AddField(
            model_name="story",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comments",
                to="stories.story",
            ),
        ),
        migrations.AddField(
            model_name="story",
            name="last_activity_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddIndex(
            model_name="story",
            index=models.Index(
                fields=["status", "-last_activity_at"],
                name="stories_sto_status_act_idx",
            ),
        ),
        migrations.RunSQL(
            sql="UPDATE stories_story SET last_activity_at = COALESCE(published_at, created_at) WHERE last_activity_at IS NULL",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
