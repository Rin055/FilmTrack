from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.MovieListView.as_view(), name='movie_list'),
    path('folders/', views.FolderListView.as_view(), name='folder_list'),
    path('discover/', views.MovieDiscoverView.as_view(), name='movie_discover'),
    path('movie/<int:pk>/', views.MovieDetailView.as_view(), name='movie_detail'),
    path('movie/<int:pk>/set-status/', views.set_movie_status, name='movie_set_status'),
    path('movie/<int:pk>/set-rating/', views.set_movie_rating, name='movie_set_rating'),
    path('movie/<int:pk>/remove-rating/', views.remove_movie_rating, name='movie_remove_rating'),
    path('movie/<int:pk>/comment/', views.add_movie_comment, name='movie_add_comment'),
    path('movie/<int:pk>/comment/<int:comment_id>/delete/', views.delete_movie_comment, name='movie_delete_comment'),
    path('movie/add/', views.MovieCreateView.as_view(), name='movie_add'),
    path('movie/<int:pk>/delete/', views.delete_movie, name='movie_delete'),
    path('movie/<int:pk>/favorite/', views.toggle_movie_favorite, name='movie_toggle_favorite'),
    path('movie/<int:pk>/folder/add/', views.add_movie_to_folder, name='movie_add_to_folder'),
    path('movie/<int:pk>/folder/remove/', views.remove_movie_from_folder, name='movie_remove_from_folder'),
    path('folders/create/', views.create_folder, name='folder_create'),
    path('folders/<int:pk>/rename/', views.rename_folder, name='folder_rename'),
    path('folders/<int:pk>/delete/', views.delete_folder, name='folder_delete'),
]
