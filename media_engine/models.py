from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from content.models import Fact


class BackgroundVideo(models.Model):
    """Library of background videos"""
    BACKGROUND_TYPES = [
        ('nature', 'Nature'),
        ('city', 'City Timelapse'),
        ('abstract', 'Abstract Visuals'),
        ('space', 'Space'),
        ('ocean', 'Ocean'),
    ]
    
    name = models.CharField(max_length=200)
    video_type = models.CharField(max_length=20, choices=BACKGROUND_TYPES)
    file = models.FileField(
        upload_to='backgrounds/',
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi'])]
    )
    duration = models.FloatField(help_text="Duration in seconds")
    resolution = models.CharField(max_length=20, default='1080x1920')
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['usage_count', '-last_used']
    
    def __str__(self):
        return f"{self.name} ({self.get_video_type_display()})"
    
    def mark_used(self):
        """Update usage statistics"""
        from django.utils import timezone
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save()


class VoiceProfile(models.Model):
    """TTS voice profiles for variation"""
    VOICE_GENDERS = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    TTS_PROVIDERS = [
        ('elevenlabs', 'ElevenLabs'),
        ('gtts', 'Google TTS'),
    ]
    
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=20, choices=TTS_PROVIDERS)
    voice_id = models.CharField(max_length=100, help_text="Provider-specific voice ID")
    gender = models.CharField(max_length=10, choices=VOICE_GENDERS)
    
    # Voice settings
    speed_multiplier = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.5), MaxValueValidator(2.0)]
    )
    pitch = models.IntegerField(default=0, validators=[MinValueValidator(-20), MaxValueValidator(20)])
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['usage_count', '-last_used']
    
    def __str__(self):
        return f"{self.name} ({self.get_gender_display()}) - {self.provider}"
    
    def mark_used(self):
        """Update usage statistics"""
        from django.utils import timezone
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save()


class Video(models.Model):
    """Generated videos"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Content
    fact = models.ForeignKey(Fact, on_delete=models.CASCADE, related_name='videos')
    background_video = models.ForeignKey(BackgroundVideo, on_delete=models.SET_NULL, null=True)
    voice_profile = models.ForeignKey(VoiceProfile, on_delete=models.SET_NULL, null=True)
    
    # Generated files
    audio_file = models.FileField(upload_to='audio/', blank=True, null=True)
    subtitle_file = models.FileField(upload_to='subtitles/', blank=True, null=True)
    final_video = models.FileField(
        upload_to='videos/generated/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp4'])]
    )
    
    # Video properties
    duration = models.FloatField(default=0, help_text="Duration in seconds")
    resolution = models.CharField(max_length=20, default='1080x1920')
    file_size = models.BigIntegerField(default=0, help_text="Size in bytes")
    
    # Generation metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    generation_started = models.DateTimeField(null=True, blank=True)
    generation_completed = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Subtitle settings
    subtitle_font_size = models.IntegerField(default=48)
    subtitle_position = models.CharField(max_length=20, default='center')
    subtitle_color = models.CharField(max_length=7, default='#FFFFFF')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Video #{self.id} - {self.fact.content[:30]}... ({self.status})"
    
    @property
    def is_ready(self):
        """Check if video is ready for upload"""
        return self.status == 'completed' and self.final_video


class SubtitleSegment(models.Model):
    """Individual subtitle segments for a video"""
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='subtitle_segments')
    text = models.CharField(max_length=200)
    start_time = models.FloatField(help_text="Start time in seconds")
    end_time = models.FloatField(help_text="End time in seconds")
    sequence = models.IntegerField(help_text="Order of appearance")
    
    class Meta:
        ordering = ['video', 'sequence']
        unique_together = ['video', 'sequence']
    
    def __str__(self):
        return f"{self.video.id} - Segment {self.sequence}: {self.text}"
