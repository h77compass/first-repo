from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # 文章列表页
    path('', views.PostListView.as_view(), name='post_list'),
    # 文章详情页
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    # 分类文章列表
    path('category/<int:pk>/', views.CategoryPostListView.as_view(), name='category_posts'),
    # 标签文章列表
    path('tag/<int:pk>/', views.TagPostListView.as_view(), name='tag_posts'),
    # 作者文章列表
    path('author/<int:pk>/', views.AuthorPostListView.as_view(), name='author_posts'),
    # 搜索功能
    path('search/', views.search, name='search'),
    # 评论功能
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    # 回复评论
    path('comment/<int:pk>/reply/', views.reply_comment, name='reply_comment'),
]