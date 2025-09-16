from django.contrib import admin
from .models import Post, Category, Tag, Comment

# 注册文章模型
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'publish_time', 'views')
    list_filter = ('status', 'category', 'tags', 'author', 'publish_time')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    date_hierarchy = 'publish_time'
    ordering = ('status', '-publish_time')
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'slug', 'author', 'status')
        }),
        ('内容', {
            'fields': ('content', 'excerpt')
        }),
        ('分类与标签', {
            'fields': ('category', 'tags')
        }),
        ('时间信息', {
            'fields': ('publish_time',)
        }),
    )

# 注册分类模型
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

# 注册标签模型
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

# 注册评论模型
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'content', 'created_time', 'is_active')
    list_filter = ('is_active', 'created_time')
    search_fields = ('content', 'author__username')
