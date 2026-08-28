from django.db import migrations, models
from django.db.models import Q


def dedupe_clouds(apps, schema_editor):
    SupportCloud = apps.get_model("support", "SupportCloud")
    keep: set = set()
    # Newest per sender×story; rejected rows can coexist.
    qs = SupportCloud.objects.exclude(status="rejected").order_by("-created_at")
    for cloud in qs:
        if cloud.from_account_id:
            key = ("a", cloud.story_id, cloud.from_account_id)
        else:
            key = ("s", cloud.story_id, cloud.from_session_id)
        if key in keep:
            cloud.delete()
        else:
            keep.add(key)


class Migration(migrations.Migration):
    dependencies = [
        ("support", "0004_phrase_image_dismiss"),
    ]

    operations = [
        migrations.RunPython(dedupe_clouds, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="supportcloud",
            name="unique_quiet_phrase_per_account_story",
        ),
        migrations.RemoveConstraint(
            model_name="supportcloud",
            name="unique_quiet_phrase_per_session_story",
        ),
        migrations.AddConstraint(
            model_name="supportcloud",
            constraint=models.UniqueConstraint(
                fields=("story", "from_account"),
                condition=Q(from_account__isnull=False) & ~Q(status="rejected"),
                name="unique_cloud_per_account_story",
            ),
        ),
        migrations.AddConstraint(
            model_name="supportcloud",
            constraint=models.UniqueConstraint(
                fields=("story", "from_session"),
                condition=Q(from_session__isnull=False) & ~Q(status="rejected"),
                name="unique_cloud_per_session_story",
            ),
        ),
    ]
