from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('movies', '0010_make_description_required'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movie',
            name='review',
        ),
    ]
