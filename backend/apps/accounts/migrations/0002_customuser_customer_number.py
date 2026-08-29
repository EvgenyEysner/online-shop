from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="customer_number",
            field=models.CharField(
                blank=True,
                max_length=16,
                null=True,
                unique=True,
                verbose_name="Kundennummer",
            ),
        ),
    ]
