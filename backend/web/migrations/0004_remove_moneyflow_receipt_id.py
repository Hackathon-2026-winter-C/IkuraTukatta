from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("web", "0003_remove_moneyflow_receipt_id"),
    ]

    operations = [
        migrations.RunPython(migrations.RunPython.noop),
    ]
