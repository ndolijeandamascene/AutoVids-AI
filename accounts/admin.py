from django.contrib import admin
from .models import TikTokAccount, UploadSchedule, UploadLog, AutomationSettings


@admin.register(TikTokAccount)
class TikTokAccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'status', 'is_automation_enabled', 'account_age_days', 'risk_score', 'total_uploads']
    list_filter = ['status', 'is_automation_enabled']
    search_fields = ['username', 'email', 'display_name']
    ordering = ['-created_at']
    readonly_fields = ['account_age_days', 'risk_score', 'total_uploads', 'session_last_updated', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Account Info', {
            'fields': ('username', 'display_name', 'email')
        }),
        ('Status', {
            'fields': ('status', 'is_automation_enabled', 'account_created_date', 'automation_start_date')
        }),
        ('Upload Limits', {
            'fields': ('max_videos_per_day', 'min_hours_between_posts')
        }),
        ('Session Management', {
            'fields': ('session_is_valid', 'session_last_updated'),
            'classes': ('collapse',)
        }),
        ('Safety & Risk', {
            'fields': ('risk_score', 'last_upload_time', 'consecutive_upload_days', 'total_uploads')
        }),
        ('Analytics', {
            'fields': ('total_views', 'total_likes', 'total_shares', 'follower_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['enable_automation', 'disable_automation', 'calculate_risk']
    
    def enable_automation(self, request, queryset):
        for account in queryset:
            if account.can_enable_automation:
                account.is_automation_enabled = True
                account.save()
        self.message_user(request, f"Enabled automation for {queryset.count()} accounts")
    enable_automation.short_description = "Enable automation"
    
    def disable_automation(self, request, queryset):
        queryset.update(is_automation_enabled=False)
        self.message_user(request, f"Disabled automation for {queryset.count()} accounts")
    disable_automation.short_description = "Disable automation"
    
    def calculate_risk(self, request, queryset):
        for account in queryset:
            account.calculate_risk_score()
        self.message_user(request, f"Calculated risk for {queryset.count()} accounts")
    calculate_risk.short_description = "Calculate risk score"


@admin.register(UploadSchedule)
class UploadScheduleAdmin(admin.ModelAdmin):
    list_display = ['id', 'account', 'scheduled_time', 'status', 'retry_count', 'actual_upload_time']
    list_filter = ['status', 'account']
    search_fields = ['account__username', 'video__fact__content']
    ordering = ['-scheduled_time']
    readonly_fields = ['upload_started', 'upload_completed', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Schedule Info', {
            'fields': ('account', 'video', 'caption', 'scheduled_time', 'actual_upload_time')
        }),
        ('Status', {
            'fields': ('status', 'retry_count', 'max_retries', 'error_message')
        }),
        ('Upload Timing', {
            'fields': ('upload_started', 'upload_completed', 'pre_upload_delay')
        }),
        ('TikTok Response', {
            'fields': ('tiktok_video_id', 'tiktok_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UploadLog)
class UploadLogAdmin(admin.ModelAdmin):
    list_display = ['upload_schedule', 'attempt_number', 'success', 'started_at', 'completed_at']
    list_filter = ['success']
    search_fields = ['upload_schedule__account__username', 'error_type']
    ordering = ['-started_at']
    readonly_fields = ['started_at', 'completed_at']


@admin.register(AutomationSettings)
class AutomationSettingsAdmin(admin.ModelAdmin):
    list_display = ['is_active', 'enable_human_behavior', 'max_daily_uploads_global', 'enable_overnight_pause']
    
    fieldsets = (
        ('System Status', {
            'fields': ('is_active',)
        }),
        ('Human Behavior Simulation', {
            'fields': (
                'enable_human_behavior',
                'random_delay_min_seconds',
                'random_delay_max_seconds',
                'enable_mouse_movement',
                'mouse_speed_min',
                'mouse_speed_max'
            )
        }),
        ('Page Interaction', {
            'fields': ('page_load_wait_min', 'page_load_wait_max')
        }),
        ('Safety Controls', {
            'fields': (
                'max_daily_uploads_global',
                'enable_overnight_pause',
                'overnight_start_hour',
                'overnight_end_hour'
            )
        }),
        ('Random Breaks', {
            'fields': ('enable_random_breaks', 'break_probability')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not AutomationSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False
