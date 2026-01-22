from django.contrib import admin
from .models import ContentCategory, HookTemplate, Fact, Caption, ContentBlacklist


@admin.register(ContentCategory)
class ContentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(HookTemplate)
class HookTemplateAdmin(admin.ModelAdmin):
    list_display = ['template', 'hook_type', 'is_active', 'usage_count', 'last_used']
    list_filter = ['hook_type', 'is_active']
    search_fields = ['template']
    ordering = ['usage_count', '-last_used']
    readonly_fields = ['usage_count', 'last_used']


@admin.register(Fact)
class FactAdmin(admin.ModelAdmin):
    list_display = ['content_preview', 'category', 'is_approved', 'is_used', 'quality_score', 'created_at']
    list_filter = ['category', 'is_approved', 'is_used', 'ai_provider']
    search_fields = ['content', 'full_script']
    ordering = ['-created_at']
    readonly_fields = ['content_hash', 'used_in_video', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('category', 'content', 'hook_used', 'full_script')
        }),
        ('AI Generation', {
            'fields': ('ai_provider', 'generation_prompt')
        }),
        ('Quality Control', {
            'fields': ('is_approved', 'quality_score', 'similarity_checked', 'content_hash')
        }),
        ('Usage', {
            'fields': ('is_used', 'used_in_video')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(Caption)
class CaptionAdmin(admin.ModelAdmin):
    list_display = ['caption_preview', 'fact_preview', 'style', 'is_used', 'performance_score']
    list_filter = ['style', 'is_used']
    search_fields = ['text', 'hashtags']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def caption_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    caption_preview.short_description = 'Caption'
    
    def fact_preview(self, obj):
        return obj.fact.content[:30] + '...'
    fact_preview.short_description = 'Fact'


@admin.register(ContentBlacklist)
class ContentBlacklistAdmin(admin.ModelAdmin):
    list_display = ['phrase', 'blacklist_type', 'is_active', 'created_at']
    list_filter = ['blacklist_type', 'is_active']
    search_fields = ['phrase']
    ordering = ['blacklist_type', 'phrase']
