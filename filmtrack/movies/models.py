from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Genre(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Movie(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Not Chosen Yet'),
        ('watching', 'Watching'),
        ('watched', 'Watched'),
    ]

    title = models.CharField(max_length=200)
    release_year = models.IntegerField()
    genres = models.ManyToManyField(Genre, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='planned')
    rating = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    description = models.TextField()
    poster_url = models.URLField(blank=True, null=True)
    is_favorite = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} ({self.release_year})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'title', 'release_year'],
                name='unique_user_movie_title_year'
            ),
        ]

class Rating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movie_ratings')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['movie', 'user'], name='unique_movie_rating_per_user')
        ]

    def __str__(self):
        return f"{self.movie.title} - {self.rating}/10 by {self.user.username}"

class Comment(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movie_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} on {self.movie.title}"

class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='movie_folders')
    name = models.CharField(max_length=60)
    movies = models.ManyToManyField(Movie, related_name='folders', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='unique_folder_name_per_user')
        ]

    def __str__(self):
        return f"{self.name} ({self.user.username})"
