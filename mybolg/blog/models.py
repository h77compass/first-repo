from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

# 文章分类模型
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='分类名称')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    modified_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    description = models.TextField(max_length=500, blank=True, verbose_name='分类描述')

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']

    def __str__(self):
        return self.name

# 文章标签模型
class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='标签名称')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    modified_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = verbose_name
        ordering = ['-created_time']

    def __str__(self):
        return self.name

# 博客文章模型
class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('published', '已发布'),
    )
    
    title = models.CharField(max_length=200, verbose_name='标题')
    slug = models.SlugField(max_length=200, unique_for_date='publish_time', verbose_name='短链接')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts', verbose_name='作者')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts', verbose_name='分类')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name='标签')
    excerpt = models.TextField(max_length=500, blank=True, verbose_name='摘要')
    content = models.TextField(verbose_name='内容')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    modified_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    publish_time = models.DateTimeField(blank=True, null=True, verbose_name='发布时间')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    views = models.PositiveIntegerField(default=0, editable=False, verbose_name='浏览量')
    featured_image = models.ImageField(upload_to='post_images/', blank=True, null=True, verbose_name='特色图片')
    
    class Meta:
        verbose_name = '文章'
        verbose_name_plural = verbose_name
        ordering = ['-publish_time', '-created_time']

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.publish_time:
            self.publish_time = timezone.now()
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.id})
    
    def increase_views(self):
        self.views += 1
        self.save(update_fields=['views'])

# 评论模型
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='文章')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name='评论者')
    content = models.TextField(verbose_name='评论内容')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    modified_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='父评论')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = verbose_name
        ordering = ['created_time']

    def __str__(self):
        return f'Comment by {self.author} on {self.post}'
