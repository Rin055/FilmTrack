from rest_framework import serializers
from .models import Movie, Genre

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name']

class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    genre_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Genre.objects.all(), source='genres'
    )

    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'release_year', 'genres', 'genre_ids',
            'status', 'rating', 'description', 'poster_url', 'user'
        ]
        read_only_fields = ['user']

    def validate_rating(self, value):
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError("Rating must be between 0 and 10")
        return value
