from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("support", "0003_quietphrase_text_en"),
    ]

    operations = [
        migrations.AddField(
            model_name="quietphrase",
            name="image",
            field=models.FileField(blank=True, null=True, upload_to="quiet_phrases/"),
        ),
        migrations.AddField(
            model_name="supportcloud",
            name="dismissed_by_author",
            field=models.BooleanField(default=False),
        ),
    ]
