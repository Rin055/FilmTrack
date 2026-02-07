from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0006_dedup_movies_and_unique_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
