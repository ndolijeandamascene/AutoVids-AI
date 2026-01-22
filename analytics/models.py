from django.db import models
from django.utils import timezone


class VideoPerformance(models.Model):
    """Track performance metrics for uploaded videos"""
    upload_schedule = models.OneToOneField(
        'accounts.UploadSchedule',
        on_delete=models.CASCADE,
        related_name='performance'
    )
    
    # Engagement metrics
    views = models.BigIntegerField(default=0)
    likes = models.BigIntegerField(default=0)
    comments = models.BigIntegerField(default=0)
    shares = models.BigIntegerField(default=0)
    saves = models.BigIntegerField(default=0)
    
    # Calculated metrics
    engagement_rate = models.FloatField(default=0.0, help_text="(likes + comments + shares) / views")
    watch_time_avg = models.FloatField(default=0.0, help_text="Average watch time in seconds")
    completion_rate = models.FloatField(default=0.0, help_text="Percentage who watched to end")
    
    # Growth metrics
    followers_gained = models.IntegerField(default=0)
    profile_views = models.IntegerField(default=0)
    
    # Time-based tracking
    first_hour_views = models.IntegerField(default=0)
    first_day_views = models.IntegerField(default=0)
    
    # Last update
    last_synced = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-views']
    
    def __str__(self):
        return f"Performance: {self.upload_schedule.video.fact.content[:30]}... ({self.views} views)"
    
    def calculate_engagement_rate(self):
        """Calculate engagement rate"""
        if self.views > 0:
            self.engagement_rate = ((self.likes + self.comments + self.shares) / self.views) * 100
        else:
            self.engagement_rate = 0.0
        self.save()
        return self.engagement_rate


class DailyAnalytics(models.Model):
    """Daily aggregated analytics per account"""
    account = models.ForeignKey('accounts.TikTokAccount', on_delete=models.CASCADE, related_name='daily_analytics')
    date = models.DateField(db_index=True)
    
    # Daily metrics
    videos_uploaded = models.IntegerField(default=0)
    total_views = models.BigIntegerField(default=0)
    total_likes = models.BigIntegerField(default=0)
    total_comments = models.BigIntegerField(default=0)
    total_shares = models.BigIntegerField(default=0)
    
    # Account growth
    followers_start = models.IntegerField(default=0)
    followers_end = models.IntegerField(default=0)
    followers_gained = models.IntegerField(default=0)
    
    # Engagement
    avg_engagement_rate = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['account', 'date']
        verbose_name_plural = "Daily Analytics"
    
    def __str__(self):
        return f"{self.account.username} - {self.date}"


class ContentPerformanceInsight(models.Model):
    """Insights about what content performs best"""
    category = models.ForeignKey('content.ContentCategory', on_delete=models.CASCADE, related_name='insights')
    
    # Performance aggregates
    total_videos = models.IntegerField(default=0)
    avg_views = models.FloatField(default=0.0)
    avg_engagement_rate = models.FloatField(default=0.0)
    
    # Best performing
    best_video = models.ForeignKey(
        'media_engine.Video',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    best_video_views = models.BigIntegerField(default=0)
    
    # Trends
    trend_direction = models.CharField(
        max_length=20,
        choices=[('up', 'Trending Up'), ('down', 'Trending Down'), ('stable', 'Stable')],
        default='stable'
    )
    
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-avg_views']
    
    def __str__(self):
        return f"{self.category.name} - Avg Views: {self.avg_views:.0f}"


class HookPerformanceInsight(models.Model):
    """Track which hook types perform best"""
    hook_type = models.CharField(max_length=20, db_index=True)
    
    # Usage stats
    total_uses = models.IntegerField(default=0)
    
    # Performance
    avg_views = models.FloatField(default=0.0)
    avg_engagement_rate = models.FloatField(default=0.0)
    avg_completion_rate = models.FloatField(default=0.0)
    
    # Best performing hook
    best_hook_template = models.ForeignKey(
        'content.HookTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-avg_engagement_rate']
    
    def __str__(self):
        return f"{self.hook_type} - Avg Engagement: {self.avg_engagement_rate:.2f}%"


class SystemLog(models.Model):
    """System-wide logs for monitoring"""
    LOG_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    LOG_CATEGORIES = [
        ('content_generation', 'Content Generation'),
        ('video_creation', 'Video Creation'),
        ('upload', 'Upload'),
        ('automation', 'Automation'),
        ('analytics', 'Analytics'),
        ('system', 'System'),
    ]
    
    level = models.CharField(max_length=20, choices=LOG_LEVELS, db_index=True)
    category = models.CharField(max_length=30, choices=LOG_CATEGORIES, db_index=True)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # Context
    account = models.ForeignKey(
        'accounts.TikTokAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs'
    )
    video = models.ForeignKey(
        'media_engine.Video',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['level', '-created_at']),
            models.Index(fields=['category', '-created_at']),
        ]
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.category}: {self.message[:50]}"
