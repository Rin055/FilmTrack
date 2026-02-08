from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Avg, Max, Count, Prefetch
from django.db import IntegrityError
from .models import Movie, Rating, Comment, Genre, Folder
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

class MovieListView(LoginRequiredMixin, ListView):
    model = Movie
    template_name = 'movies/movie_list.html'
    context_object_name = 'movies'

    def get_queryset(self):
        if self.request.user.is_superuser:
            queryset = Movie.objects.all()
        else:
            queryset = Movie.objects.filter(user=self.request.user)

        folder_id = self.request.GET.get('folder', '').strip()
        favorites_only = self.request.GET.get('favorites', '').strip() == '1'
        status_filter = self.request.GET.get('status', '').strip()
        sort_key = self.request.GET.get('sort', '').strip() or 'newest'

        if favorites_only:
            queryset = queryset.filter(is_favorite=True)

        if status_filter in {'planned', 'watching', 'watched'}:
            queryset = queryset.filter(status=status_filter)

        if folder_id.isdigit():
            queryset = queryset.filter(folders__id=int(folder_id), folders__user=self.request.user)

        if sort_key == 'oldest':
            queryset = queryset.order_by('id')
        elif sort_key == 'title':
            queryset = queryset.order_by('title', 'release_year')
        else:
            queryset = queryset.order_by('-id')

        folder_qs = Folder.objects.filter(user=self.request.user).only('id', 'name')
        return queryset.distinct().prefetch_related(Prefetch('folders', queryset=folder_qs), 'genres')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_superuser:
            all_qs = Movie.objects.all()
        else:
            all_qs = Movie.objects.filter(user=self.request.user)

        recent_badge_ids = list(all_qs.order_by('-id').values_list('id', flat=True)[:3])
        context['recent_badge_ids'] = set(recent_badge_ids)
        context['folders'] = (
            Folder.objects.filter(user=self.request.user)
            .annotate(movie_count=Count('movies'))
            .order_by('name')
        )
        context['favorites_count'] = all_qs.filter(is_favorite=True).count()
        context['selected_folder'] = self.request.GET.get('folder', '').strip()
        context['favorites_only'] = self.request.GET.get('favorites', '').strip() == '1'
        context['selected_status'] = self.request.GET.get('status', '').strip()
        context['selected_sort'] = self.request.GET.get('sort', '').strip() or 'newest'
        context['folders'] = (
            Folder.objects.filter(user=self.request.user)
            .only('id', 'name')
            .order_by('name')
        )
        return context

class FolderListView(LoginRequiredMixin, TemplateView):
    template_name = 'movies/folder_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_superuser:
            all_qs = Movie.objects.all()
        else:
            all_qs = Movie.objects.filter(user=self.request.user)

        context['folders'] = (
            Folder.objects.filter(user=self.request.user)
            .annotate(movie_count=Count('movies'))
            .order_by('name')
        )
        context['favorites_count'] = all_qs.filter(is_favorite=True).count()
        context['watching_count'] = all_qs.filter(status='watching').count()
        context['watched_count'] = all_qs.filter(status='watched').count()
        context['planned_count'] = all_qs.filter(status='planned').count()
        return context

class MovieDiscoverView(LoginRequiredMixin, ListView):
    model = Movie
    template_name = 'movies/movie_discover.html'
    context_object_name = 'movies'

    def get_queryset(self):
        queryset = Movie.objects.all()
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(title__icontains=query)
        genre_id = self.request.GET.get('genre', '').strip()
        if genre_id.isdigit():
            queryset = queryset.filter(genres__id=int(genre_id))
        year_value = self.request.GET.get('year', '').strip()
        if year_value.isdigit():
            queryset = queryset.filter(release_year=int(year_value))
        latest_ids = (
            queryset.values('title', 'release_year')
            .annotate(latest_id=Max('id'))
            .values_list('latest_id', flat=True)
        )
        return (
            queryset.filter(id__in=latest_ids)
            .distinct()
            .annotate(avg_rating=Avg('ratings__rating'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_movies = Movie.objects.filter(user=self.request.user).only('id', 'title', 'release_year', 'status', 'is_favorite')
        user_status_map = {
            (movie.title, movie.release_year): movie.status
            for movie in user_movies
        }
        user_favorite_map = {
            (movie.title, movie.release_year): movie.is_favorite
            for movie in user_movies
        }
        recent_keys = set(
            user_movies.order_by('-id').values_list('title', 'release_year')[:6]
        )
        for movie in context['movies']:
            movie.user_status = user_status_map.get((movie.title, movie.release_year), 'planned')
            movie.user_recent = (movie.title, movie.release_year) in recent_keys
            movie.user_in_collection = (movie.title, movie.release_year) in user_status_map
            movie.user_favorite = user_favorite_map.get((movie.title, movie.release_year), False)
        context['search_query'] = self.request.GET.get('q', '').strip()
        context['selected_genre'] = self.request.GET.get('genre', '').strip()
        context['selected_year'] = self.request.GET.get('year', '').strip()
        context['genres'] = Genre.objects.order_by('name')
        context['years'] = (
            Movie.objects.order_by('-release_year')
            .values_list('release_year', flat=True)
            .distinct()
        )
        return context

class MovieDetailView(LoginRequiredMixin, DetailView):
    model = Movie
    template_name = 'movies/movie_detail.html'

    def get_queryset(self):
        return Movie.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = self.object
        comments = (
            movie.comments.select_related('user')
            .filter(parent__isnull=True)
            .prefetch_related('replies__user', 'replies__replies__user')
        )
        def count_descendants(node):
            total = 0
            for reply in node.replies.all():
                total += 1 + count_descendants(reply)
            return total
        for comment in comments:
            comment.reply_count = count_descendants(comment)
        context['comments'] = comments
        context['user_replied_ids'] = set(
            Comment.objects.filter(movie=movie, user=self.request.user, parent__isnull=False)
            .values_list('parent_id', flat=True)
        )
        context['user_rating'] = Rating.objects.filter(movie=movie, user=self.request.user).first()
        context['avg_rating'] = movie.ratings.aggregate(avg=Avg('rating'))['avg']
        context['rating_count'] = movie.ratings.count()
        context['rating_options'] = range(1, 11)
        return context

class MovieCreateView(LoginRequiredMixin, CreateView):
    model = Movie
    template_name = 'movies/movie_form.html'
    fields = ['title', 'release_year', 'genres', 'status', 'rating', 'description', 'poster_url']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

@login_required
def delete_movie(request, pk):
    if request.method != 'POST':
        return redirect('movies:movie_detail', pk=pk)

    movie = get_object_or_404(Movie, pk=pk)
    if movie.user_id == request.user.id:
        movie.delete()
    else:
        owned_movie = Movie.objects.filter(
            user=request.user,
            title=movie.title,
            release_year=movie.release_year,
        ).first()
        if owned_movie:
            owned_movie.delete()
    return redirect(request.POST.get('next') or 'movies:movie_list')

@login_required
def set_movie_status(request, pk):
    if request.method != 'POST':
        return redirect('movies:movie_discover')

    movie = get_object_or_404(Movie, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    allowed_statuses = {choice[0] for choice in Movie.STATUS_CHOICES}
    status = request.POST.get('status', '').strip()

    if status not in allowed_statuses:
        return redirect(request.POST.get('next') or 'movies:movie_discover')

    if request.user.is_superuser or movie.user_id == request.user.id:
        movie.status = status
        movie.save(update_fields=['status'])
        if is_ajax:
            return JsonResponse({'status': status, 'status_display': movie.get_status_display()})
    else:
        owned_movie, created = Movie.objects.get_or_create(
            user=request.user,
            title=movie.title,
            release_year=movie.release_year,
            defaults={
                'status': status,
                'rating': None,
                'description': movie.description,
                'poster_url': movie.poster_url,
            },
        )
        if not created:
            owned_movie.status = status
            owned_movie.poster_url = movie.poster_url
            owned_movie.save(update_fields=['status', 'poster_url'])
        owned_movie.genres.set(movie.genres.all())
        if is_ajax:
            return JsonResponse({'status': owned_movie.status, 'status_display': owned_movie.get_status_display()})

    return redirect(request.POST.get('next') or 'movies:movie_discover')

@login_required
def set_movie_rating(request, pk):
    if request.method != 'POST':
        return redirect('movies:movie_detail', pk=pk)

    movie = get_object_or_404(Movie, pk=pk)
    rating_value = request.POST.get('rating', '').strip()
    try:
        rating_value = int(rating_value)
    except ValueError:
        return redirect(request.POST.get('next') or 'movies:movie_detail', pk=pk)

    if rating_value < 1 or rating_value > 10:
        return redirect(request.POST.get('next') or 'movies:movie_detail', pk=pk)

    rating_obj, created = Rating.objects.update_or_create(
        movie=movie,
        user=request.user,
        defaults={'rating': rating_value},
    )

    if request.user.is_superuser or movie.user_id == request.user.id:
        movie.rating = rating_value
        movie.save(update_fields=['rating'])
    else:
        owned_movie, owned_created = Movie.objects.get_or_create(
            user=request.user,
            title=movie.title,
            release_year=movie.release_year,
            defaults={
                'status': 'planned',
                'rating': rating_value,
                'description': movie.description,
                'poster_url': movie.poster_url,
            },
        )
        if not owned_created:
            owned_movie.rating = rating_value
            owned_movie.poster_url = movie.poster_url
            owned_movie.save(update_fields=['rating', 'poster_url'])
        owned_movie.genres.set(movie.genres.all())
    return redirect(request.POST.get('next') or 'movies:movie_detail', pk=pk)

@login_required
def remove_movie_rating(request, pk):
    if request.method != 'POST':
        return redirect('movies:movie_detail', pk=pk)

    movie = get_object_or_404(Movie, pk=pk)
    Rating.objects.filter(movie=movie, user=request.user).delete()
    if request.user.is_superuser or movie.user_id == request.user.id:
        movie.rating = None
        movie.save(update_fields=['rating'])
    else:
        owned_movie = Movie.objects.filter(
            user=request.user,
            title=movie.title,
            release_year=movie.release_year,
        ).first()
        if owned_movie:
            owned_movie.rating = None
            owned_movie.save(update_fields=['rating'])
    return redirect(request.POST.get('next') or 'movies:movie_detail', pk=pk)

@login_required
def add_movie_comment(request, pk):
    if request.method != 'POST':
        return redirect('movies:movie_detail', pk=pk)

    movie = get_object_or_404(Movie, pk=pk)
    text = request.POST.get('comment', '').strip()
    parent_id = request.POST.get('parent_id')
    parent = None
    if parent_id:
        parent = Comment.objects.filter(movie=movie, pk=parent_id).first()
    if text:
        Comment.objects.create(movie=movie, user=request.user, text=text, parent=parent)
    return redirect(request.POST.get('next') or 'movies:movie_detail', pk=pk)

@login_required
def delete_movie_comment(request, pk, comment_id):
    if request.method != 'POST':
        return redirect('movies:movie_detail', pk=pk)

    movie = get_object_or_404(Movie, pk=pk)
    comment = get_object_or_404(Comment, pk=comment_id, movie=movie)
    if comment.user_id == request.user.id or request.user.is_superuser:
        comment.is_deleted = True
        comment.text = 'Deleted'
        comment.save(update_fields=['is_deleted', 'text'])
    return redirect(request.POST.get('next') or 'movies:movie_detail', pk=pk)

@login_required
def create_folder(request):
    if request.method != 'POST':
        return redirect('movies:movie_list')

    name = request.POST.get('name', '').strip()
    if name:
        Folder.objects.get_or_create(user=request.user, name=name)
    return redirect(request.POST.get('next') or 'movies:movie_list')

@login_required
def rename_folder(request, pk):
    if request.method != 'POST':
        return redirect('movies:folder_list')

    folder = get_object_or_404(Folder, pk=pk, user=request.user)
    name = request.POST.get('name', '').strip()
    if name and name != folder.name:
        folder.name = name
        try:
            folder.save(update_fields=['name'])
        except IntegrityError:
            pass
    return redirect(request.POST.get('next') or 'movies:folder_list')

@login_required
def delete_folder(request, pk):
    if request.method != 'POST':
        return redirect('movies:folder_list')

    folder = get_object_or_404(Folder, pk=pk, user=request.user)
    folder.delete()
    return redirect(request.POST.get('next') or 'movies:folder_list')

@login_required
def add_movie_to_folder(request, pk):
    if request.method != 'POST':
        return redirect('movies:movie_list')

    folder_id = request.POST.get('folder_id', '').strip()
    if not folder_id.isdigit():
        return redirect(request.POST.get('next') or 'movies:movie_list')

    movie = get_object_or_404(Movie, pk=pk)
    folder = get_object_or_404(Folder, pk=int(folder_id), user=request.user)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.user.is_superuser or movie.user_id == request.user.id:
        folder.movies.add(movie)
        if is_ajax:
            return JsonResponse({'ok': True, 'folder_name': folder.name, 'folder_id': folder.id})
    elif is_ajax:
        return JsonResponse({'ok': False}, status=403)
    return redirect(request.POST.get('next') or 'movies:movie_list')

@login_required
def remove_movie_from_folder(request, pk):
    if request.method != 'POST':
        return redirect('movies:movie_list')

    folder_id = request.POST.get('folder_id', '').strip()
    if not folder_id.isdigit():
        return redirect(request.POST.get('next') or 'movies:movie_list')

    movie = get_object_or_404(Movie, pk=pk)
    folder = get_object_or_404(Folder, pk=int(folder_id), user=request.user)

    if request.user.is_superuser or movie.user_id == request.user.id:
        folder.movies.remove(movie)
    return redirect(request.POST.get('next') or 'movies:movie_list')

@login_required
def toggle_movie_favorite(request, pk):
    if request.method != 'POST':
        return redirect('movies:movie_list')

    movie = get_object_or_404(Movie, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if request.user.is_superuser or movie.user_id == request.user.id:
        movie.is_favorite = not movie.is_favorite
        movie.save(update_fields=['is_favorite'])
        if is_ajax:
            return JsonResponse({'is_favorite': movie.is_favorite})
    else:
        owned_movie, created = Movie.objects.get_or_create(
            user=request.user,
            title=movie.title,
            release_year=movie.release_year,
            defaults={
                'status': 'planned',
                'rating': None,
                'description': movie.description,
                'poster_url': movie.poster_url,
                'is_favorite': True,
            },
        )
        if not created:
            owned_movie.is_favorite = not owned_movie.is_favorite
            owned_movie.poster_url = movie.poster_url
            owned_movie.save(update_fields=['is_favorite', 'poster_url'])
        owned_movie.genres.set(movie.genres.all())
        if is_ajax:
            return JsonResponse({'is_favorite': owned_movie.is_favorite})
    return redirect(request.POST.get('next') or 'movies:movie_list')
