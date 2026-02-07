from django.db import migrations, models
from django.db.models import Q


def fill_missing_descriptions(apps, schema_editor):
    Movie = apps.get_model('movies', 'Movie')
    missing = Movie.objects.filter(Q(description__isnull=True) | Q(description__exact=''))
    for movie in missing:
        movie.description = f"{movie.title} ({movie.release_year}) description pending."
        movie.save(update_fields=['description'])


class Migration(migrations.Migration):
    dependencies = [
        ('movies', '0009_folder_and_favorite'),
    ]

    operations = [
        migrations.RunPython(fill_missing_descriptions, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='movie',
            name='description',
            field=models.TextField(),
        ),
    ]
