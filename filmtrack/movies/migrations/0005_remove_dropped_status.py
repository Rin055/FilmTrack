from django.db import migrations


def forwards(apps, schema_editor):
    Movie = apps.get_model('movies', 'Movie')
    Movie.objects.filter(status='dropped').update(status='planned')


class Migration(migrations.Migration):
    dependencies = [
        ('movies', '0004_comment_is_deleted'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
