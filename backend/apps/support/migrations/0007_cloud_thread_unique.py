from django.db import migrations


def backfill_thread_root(apps, schema_editor):
    from django.db.models import Count

    SupportCloud = apps.get_model("support", "SupportCloud")
    Story = apps.get_model("stories", "Story")
    stories = {row.id: row.parent_id for row in Story.objects.only("id", "parent_id")}
    for cloud in SupportCloud.objects.only("id", "story_id").iterator():
        parent_id = stories.get(cloud.story_id)
        root_id = parent_id or cloud.story_id
        SupportCloud.objects.filter(pk=cloud.id).update(thread_root_id=root_id)

    def _keep_oldest(sender_field: str) -> None:
        dupes = (
            SupportCloud.objects.exclude(status="rejected")
            .exclude(thread_root_id=None)
            .exclude(**{f"{sender_field}__isnull": True})
            .values("thread_root_id", sender_field)
            .annotate(n=Count("id"))
            .filter(n__gt=1)
        )
        for row in dupes:
            qs = (
                SupportCloud.objects.filter(
                    thread_root_id=row["thread_root_id"],
                    **{sender_field: row[sender_field]},
                )
                .exclude(status="rejected")
                .order_by("created_at", "id")
            )
            keep_id = qs.values_list("id", flat=True).first()
            qs.exclude(id=keep_id).update(status="rejected")

    _keep_oldest("from_account_id")
    _keep_oldest("from_session_id")


class Migration(migrations.Migration):

    dependencies = [
        ("support", "0006_cloud_one_per_thread"),
    ]

    operations = [
        migrations.RunPython(backfill_thread_root, migrations.RunPython.noop),
    ]
