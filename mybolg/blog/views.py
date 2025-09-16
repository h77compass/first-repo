from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Post, Category, Tag, Comment

# 文章列表视图
class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    queryset = Post.objects.filter(status='published').order_by('-publish_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['tags'] = Tag.objects.filter(is_active=True)
        context['recent_posts'] = Post.objects.filter(status='published').order_by('-publish_time')[:5]
        return context

# 文章详情视图
class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return Post.objects.filter(status='published')
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.object.increase_views()
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['tags'] = Tag.objects.filter(is_active=True)
        context['recent_posts'] = Post.objects.filter(status='published').order_by('-publish_time')[:5]
        context['comments'] = self.object.comments.filter(is_active=True, parent=None).order_by('-created_time')
        
        # 获取上一篇文章
        prev_posts = Post.objects.filter(status='published', publish_time__lt=self.object.publish_time).order_by('-publish_time')
        context['prev_post'] = prev_posts.first()
        
        # 获取下一篇文章
        next_posts = Post.objects.filter(status='published', publish_time__gt=self.object.publish_time).order_by('publish_time')
        context['next_post'] = next_posts.first()
        
        return context

# 分类文章列表视图
class CategoryPostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, pk=self.kwargs.get('pk'), is_active=True)
        return Post.objects.filter(category=self.category, status='published').order_by('-publish_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['tags'] = Tag.objects.filter(is_active=True)
        context['recent_posts'] = Post.objects.filter(status='published').order_by('-publish_time')[:5]
        context['current_category'] = self.category
        return context

# 标签文章列表视图
class TagPostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        self.tag = get_object_or_404(Tag, pk=self.kwargs.get('pk'), is_active=True)
        return Post.objects.filter(tags=self.tag, status='published').order_by('-publish_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['tags'] = Tag.objects.filter(is_active=True)
        context['recent_posts'] = Post.objects.filter(status='published').order_by('-publish_time')[:5]
        context['current_tag'] = self.tag
        return context

# 作者文章列表视图
class AuthorPostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        self.author = get_object_or_404(User, pk=self.kwargs.get('pk'))
        return Post.objects.filter(author=self.author, status='published').order_by('-publish_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['tags'] = Tag.objects.filter(is_active=True)
        context['recent_posts'] = Post.objects.filter(status='published').order_by('-publish_time')[:5]
        context['current_author'] = self.author
        return context

# 搜索功能视图
def search(request):
    if request.method == 'GET' and 'q' in request.GET:
        query = request.GET.get('q')
        results = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) | 
            Q(excerpt__icontains=query)
        ).filter(status='published').order_by('-publish_time')
        
        context = {
            'posts': results,
            'query': query,
            'categories': Category.objects.filter(is_active=True),
            'tags': Tag.objects.filter(is_active=True),
            'recent_posts': Post.objects.filter(status='published').order_by('-publish_time')[:5]
        }
        
        return render(request, 'blog/search_results.html', context)
    
    return redirect('blog:post_list')

# 添加评论视图
def add_comment(request, pk):
    if request.method == 'POST' and request.user.is_authenticated:
        post = get_object_or_404(Post, pk=pk, status='published')
        content = request.POST.get('content')
        
        if content:
            comment = Comment(post=post, author=request.user, content=content)
            comment.save()
            messages.success(request, '评论发布成功！')
        
    return redirect('blog:post_detail', pk=pk)

# 回复评论视图
def reply_comment(request, pk):
    if request.method == 'POST' and request.user.is_authenticated:
        parent_comment = get_object_or_404(Comment, pk=pk)
        content = request.POST.get('content')
        
        if content:
            comment = Comment(
                post=parent_comment.post,
                author=request.user,
                content=content,
                parent=parent_comment
            )
            comment.save()
            messages.success(request, '回复成功！')
        
    return redirect('blog:post_detail', pk=parent_comment.post.pk)
