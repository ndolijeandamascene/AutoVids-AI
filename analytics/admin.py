from django.contrib import admin
from .models import VideoPerformance, DailyAnalytics, ContentPerformanceInsight, HookPerformanceInsight, SystemLog


@admin.register(VideoPerformance)
class VideoPerformanceAdmin(admin.ModelAdmin):
    list_display = ['video_preview', 'views', 'likes', 'engagement_rate', 'completion_rate', 'last_synced']
    list_filter = ['last_synced']
    search_fields = ['upload_schedule__video__fact__content']
    ordering = ['-views']
    readonly_fields = ['created_at', 'updated_at']
    
    def video_preview(self, obj):
        return obj.upload_schedule.video.fact.content[:40] + '...'
    video_preview.short_description = 'Video'


@admin.register(DailyAnalytics)
class DailyAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['account', 'date', 'videos_uploaded', 'total_views', 'total_likes', 'followers_gained', 'avg_engagement_rate']
    list_filter = ['account', 'date']
    search_fields = ['account__username']
    ordering = ['-date']
    readonly_fields = ['created_at']


@admin.register(ContentPerformanceInsight)
class ContentPerformanceInsightAdmin(admin.ModelAdmin):
    list_display = ['category', 'total_videos', 'avg_views', 'avg_engagement_rate', 'trend_direction', 'last_calculated']
    list_filter = ['trend_direction', 'category']
    ordering = ['-avg_views']
    readonly_fields = ['last_calculated']


@admin.register(HookPerformanceInsight)
class HookPerformanceInsightAdmin(admin.ModelAdmin):
    list_display = ['hook_type', 'total_uses', 'avg_views', 'avg_engagement_rate', 'avg_completion_rate']
    list_filter = ['hook_type']
    ordering = ['-avg_engagement_rate']
    readonly_fields = ['last_calculated']


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'level', 'category', 'message_preview', 'account', 'video']
    list_filter = ['level', 'category', 'created_at']
    search_fields = ['message', 'details']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def message_preview(self, obj):
        return obj.message[:60] + '...' if len(obj.message) > 60 else obj.message
    message_preview.short_description = 'Message'
    
    def has_add_permission(self, request):
        # Logs are created programmatically
        return False
