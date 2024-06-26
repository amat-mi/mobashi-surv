# Generated by Django 4.2.5 on 2024-04-11 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mosurv", "0010_alter_cascho_campaign_alter_cascho_school"),
    ]

    operations = [
        migrations.AlterField(
            model_name="school",
            name="code",
            field=models.CharField(
                blank=True,
                help_text="Code of the school",
                max_length=20,
                null=True,
                verbose_name="Code",
            ),
        ),
    ]
