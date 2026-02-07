from django.db import migrations, models
from django.db.models import Count, Max


def dedupe_movies(apps, schema_editor):
    Movie = apps.get_model('movies', 'Movie')
    duplicates = (
        Movie.objects.values('user_id', 'title', 'release_year')
        .annotate(max_id=Max('id'), count=Count('id'))
        .filter(count__gt=1)
    )
    for group in duplicates:
        (Movie.objects
            .filter(
                user_id=group['user_id'],
                title=group['title'],
                release_year=group['release_year'],
            )
            .exclude(id=group['max_id'])
            .delete()
        )


class Migration(migrations.Migration):
    dependencies = [
        ('movies', '0005_remove_dropped_status'),
    ]

    operations = [
        migrations.RunPython(dedupe_movies, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='movie',
            constraint=models.UniqueConstraint(
                fields=['user', 'title', 'release_year'],
                name='unique_user_movie_title_year',
            ),
        ),
    ]
