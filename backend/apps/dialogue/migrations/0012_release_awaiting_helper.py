from django.db import migrations, models


def forwards(apps, schema_editor):
    DialogueRequest = apps.get_model("dialogue", "DialogueRequest")
    DialogueRequest.objects.filter(status="awaiting_helper").update(status="pending")


class Migration(migrations.Migration):

    dependencies = [
        ("dialogue", "0011_dialogue_request_awaiting_helper"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dialoguerequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("awaiting_helper", "Awaiting helper review"),
                    ("pending", "Pending"),
                    ("accepted", "Accepted"),
                    ("declined", "Declined"),
                    ("expired", "Expired"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
