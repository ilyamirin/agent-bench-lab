# Generated migration for content_warning field

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("files", "0014_alter_subtitle_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="media",
            name="content_warning",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "None"),
                    ("violence", "Violence"),
                    ("language", "Strong Language"),
                    ("adult", "Adult Content"),
                    ("disturbing", "Disturbing Imagery"),
                    ("other", "Other"),
                ],
                default="",
                help_text="Optional content warning for this media",
                max_length=20,
            ),
        ),
    ]
