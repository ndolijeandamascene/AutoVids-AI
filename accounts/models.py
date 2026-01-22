from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta


class TikTokAccount(models.Model):
    """TikTok account management"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('banned', 'Banned'),
        ('warming', 'Warming Up'),
    ]
    
    username = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    
    # Account status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='warming')
    is_automation_enabled = models.BooleanField(default=False)
    
    # Account age tracking
    account_created_date = models.DateField(help_text="When the TikTok account was created")
    automation_start_date = models.DateField(null=True, blank=True)
    
    # Upload limits
    max_videos_per_day = models.IntegerField(default=2, validators=[MinValueValidator(1), MaxValueValidator(5)])
    min_hours_between_posts = models.IntegerField(default=8, validators=[MinValueValidator(4), MaxValueValidator(24)])
    
    # Session management
    session_data = models.JSONField(default=dict, blank=True, help_text="Encrypted session cookies")
    session_last_updated = models.DateTimeField(null=True, blank=True)
    session_is_valid = models.BooleanField(default=False)
    
    # Safety controls
    last_upload_time = models.DateTimeField(null=True, blank=True)
    consecutive_upload_days = models.IntegerField(default=0)
    total_uploads = models.IntegerField(default=0)
    
    # Risk management
    risk_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Higher score = higher risk"
    )
    last_risk_check = models.DateTimeField(auto_now=True)
    
    # Analytics
    total_views = models.BigIntegerField(default=0)
    total_likes = models.BigIntegerField(default=0)
    total_shares = models.BigIntegerField(default=0)
    follower_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"@{self.username} ({self.get_status_display()})"
    
    @property
    def account_age_days(self):
        """Calculate account age in days"""
        return (timezone.now().date() - self.account_created_date).days
    
    @property
    def can_enable_automation(self):
        """Check if account is old enough for automation"""
        from django.conf import settings
        min_age = getattr(settings, 'ACCOUNT_AGE_DAYS_BEFORE_AUTO', 7)
        return self.account_age_days >= min_age
    
    @property
    def can_upload_now(self):
        """Check if account can upload based on timing rules"""
        if not self.is_automation_enabled or self.status != 'active':
            return False
        
        if not self.last_upload_time:
            return True
        
        hours_since_last = (timezone.now() - self.last_upload_time).total_seconds() / 3600
        return hours_since_last >= self.min_hours_between_posts
    
    def calculate_risk_score(self):
        """Calculate account risk score"""
        score = 0
        
        # New account risk
        if self.account_age_days < 7:
            score += 30
        elif self.account_age_days < 14:
            score += 15
        
        # Upload frequency risk
        if self.consecutive_upload_days > 7:
            score += 20
        
        # Session validity
        if not self.session_is_valid:
            score += 25
        
        # Recent upload risk
        if self.last_upload_time:
            hours_since = (timezone.now() - self.last_upload_time).total_seconds() / 3600
            if hours_since < self.min_hours_between_posts:
                score += 30
        
        self.risk_score = min(score, 100)
        self.save()
        return self.risk_score


class UploadSchedule(models.Model):
    """Scheduled video uploads"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('uploading', 'Uploading'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    account = models.ForeignKey(TikTokAccount, on_delete=models.CASCADE, related_name='scheduled_uploads')
    video = models.ForeignKey('media_engine.Video', on_delete=models.CASCADE, related_name='upload_schedules')
    caption = models.ForeignKey('content.Caption', on_delete=models.CASCADE, related_name='upload_schedules')
    
    # Scheduling
    scheduled_time = models.DateTimeField(db_index=True)
    actual_upload_time = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Upload metadata
    upload_started = models.DateTimeField(null=True, blank=True)
    upload_completed = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # TikTok response
    tiktok_video_id = models.CharField(max_length=100, blank=True)
    tiktok_url = models.URLField(blank=True)
    
    # Human behavior simulation
    pre_upload_delay = models.IntegerField(default=0, help_text="Random delay in seconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_time']
        indexes = [
            models.Index(fields=['status', 'scheduled_time']),
            models.Index(fields=['account', 'status']),
        ]
    
    def __str__(self):
        return f"{self.account.username} - {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def is_ready_to_upload(self):
        """Check if upload should be executed now"""
        if self.status != 'scheduled':
            return False
        
        return timezone.now() >= self.scheduled_time
    
    def can_retry(self):
        """Check if upload can be retried"""
        return self.status == 'failed' and self.retry_count < self.max_retries


class UploadLog(models.Model):
    """Detailed logs of upload attempts"""
    upload_schedule = models.ForeignKey(UploadSchedule, on_delete=models.CASCADE, related_name='logs')
    
    attempt_number = models.IntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    success = models.BooleanField(default=False)
    error_type = models.CharField(max_length=100, blank=True)
    error_details = models.TextField(blank=True)
    
    # Browser automation logs
    browser_logs = models.JSONField(default=dict, blank=True)
    screenshots = models.JSONField(default=list, blank=True, help_text="Paths to debug screenshots")
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Attempt #{self.attempt_number} - {'Success' if self.success else 'Failed'}"


class AutomationSettings(models.Model):
    """Global automation settings"""
    # Human behavior simulation
    enable_human_behavior = models.BooleanField(default=True)
    random_delay_min_seconds = models.IntegerField(default=30)
    random_delay_max_seconds = models.IntegerField(default=180)
    
    # Mouse movement simulation
    enable_mouse_movement = models.BooleanField(default=True)
    mouse_speed_min = models.FloatField(default=0.5)
    mouse_speed_max = models.FloatField(default=1.5)
    
    # Page interaction delays
    page_load_wait_min = models.IntegerField(default=2)
    page_load_wait_max = models.IntegerField(default=5)
    
    # Safety controls
    max_daily_uploads_global = models.IntegerField(default=10)
    enable_overnight_pause = models.BooleanField(default=True)
    overnight_start_hour = models.IntegerField(default=23)
    overnight_end_hour = models.IntegerField(default=7)
    
    # Random inactivity
    enable_random_breaks = models.BooleanField(default=True)
    break_probability = models.FloatField(default=0.15, help_text="15% chance of taking a break day")
    
    # System
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Automation Settings"
    
    def __str__(self):
        return f"Automation Settings (Active: {self.is_active})"
