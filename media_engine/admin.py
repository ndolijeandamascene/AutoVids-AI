from django.contrib import admin
from .models import BackgroundVideo, VoiceProfile, Video, SubtitleSegment


@admin.register(BackgroundVideo)
class BackgroundVideoAdmin(admin.ModelAdmin):
    list_display = ['name', 'video_type', 'duration', 'resolution', 'usage_count', 'is_active']
    list_filter = ['video_type', 'is_active']
    search_fields = ['name']
    ordering = ['usage_count', '-last_used']
    readonly_fields = ['usage_count', 'last_used', 'created_at']


@admin.register(VoiceProfile)
class VoiceProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'gender', 'speed_multiplier', 'usage_count', 'is_active']
    list_filter = ['provider', 'gender', 'is_active']
    search_fields = ['name', 'voice_id']
    ordering = ['usage_count', '-last_used']
    readonly_fields = ['usage_count', 'last_used', 'created_at']


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'fact_preview', 'status', 'duration', 'file_size_mb', 'created_at']
    list_filter = ['status', 'background_video__video_type', 'voice_profile__gender']
    search_fields = ['fact__content']
    ordering = ['-created_at']
    readonly_fields = ['generation_started', 'generation_completed', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('fact', 'background_video', 'voice_profile')
        }),
        ('Generated Files', {
            'fields': ('audio_file', 'subtitle_file', 'final_video')
        }),
        ('Video Properties', {
            'fields': ('duration', 'resolution', 'file_size')
        }),
        ('Subtitle Settings', {
            'fields': ('subtitle_font_size', 'subtitle_position', 'subtitle_color')
        }),
        ('Generation Status', {
            'fields': ('status', 'generation_started', 'generation_completed', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def fact_preview(self, obj):
        return obj.fact.content[:40] + '...' if len(obj.fact.content) > 40 else obj.fact.content
    fact_preview.short_description = 'Fact'
    
    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "N/A"
    file_size_mb.short_description = 'File Size'


@admin.register(SubtitleSegment)
class SubtitleSegmentAdmin(admin.ModelAdmin):
    list_display = ['video', 'sequence', 'text', 'start_time', 'end_time']
    list_filter = ['video']
    search_fields = ['text']
    ordering = ['video', 'sequence']
