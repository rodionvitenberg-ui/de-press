from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dialogue", "0008_message_actions"),
    ]

    operations = [
        migrations.AddField(
            model_name="dialogue",
            name="pinned_at_author",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dialogue",
            name="pinned_at_peer",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dialogue",
            name="muted_author",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dialogue",
            name="muted_peer",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dialogue",
            name="last_read_at_author",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dialogue",
            name="last_read_at_peer",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="dialogue",
            name="unread_forced_author",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="dialogue",
            name="unread_forced_peer",
            field=models.BooleanField(default=False),
        ),
    ]
