from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class ContentCategory(models.Model):
    """Categories for facts (Psychology, Human Body, World Facts, etc.)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Content Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class HookTemplate(models.Model):
    """Hook templates to avoid repetition"""
    HOOK_TYPES = [
        ('curiosity', 'Curiosity'),
        ('shock', 'Shock'),
        ('question', 'Question'),
        ('attention', 'Attention'),
    ]
    
    hook_type = models.CharField(max_length=20, choices=HOOK_TYPES)
    template = models.CharField(max_length=200, help_text="Use {fact} as placeholder")
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['usage_count', '-last_used']
    
    def __str__(self):
        return f"{self.get_hook_type_display()}: {self.template[:50]}"
    
    def mark_used(self):
        """Update usage statistics"""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save()


class Fact(models.Model):
    """Generated facts for videos"""
    category = models.ForeignKey(ContentCategory, on_delete=models.CASCADE, related_name='facts')
    content = models.TextField(help_text="The actual fact (1-2 sentences)")
    hook_used = models.ForeignKey(HookTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    full_script = models.TextField(help_text="Hook + Fact combined")
    
    # AI Generation metadata
    ai_provider = models.CharField(max_length=50, default='openai')
    generation_prompt = models.TextField(blank=True)
    
    # Duplicate detection
    content_hash = models.CharField(max_length=64, unique=True, db_index=True)
    similarity_checked = models.BooleanField(default=False)
    
    # Usage tracking
    is_used = models.BooleanField(default=False)
    used_in_video = models.ForeignKey('media_engine.Video', on_delete=models.SET_NULL, null=True, blank=True, related_name='fact_used')
    
    # Quality control
    is_approved = models.BooleanField(default=False)
    quality_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_used', 'is_approved']),
            models.Index(fields=['category', 'is_approved']),
        ]
    
    def __str__(self):
        return f"{self.category.name}: {self.content[:50]}..."


class Caption(models.Model):
    """Generated captions for TikTok posts"""
    fact = models.ForeignKey(Fact, on_delete=models.CASCADE, related_name='captions')
    text = models.TextField(max_length=2200, help_text="TikTok caption (max 2200 chars)")
    hashtags = models.CharField(max_length=500, help_text="Comma-separated hashtags")
    
    # Variation
    style = models.CharField(max_length=50, default='engaging')
    emoji_count = models.IntegerField(default=3)
    
    # Usage
    is_used = models.BooleanField(default=False)
    performance_score = models.IntegerField(default=0, help_text="Based on video performance")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Caption for: {self.fact.content[:30]}..."


class ContentBlacklist(models.Model):
    """Words/phrases to avoid in content generation"""
    BLACKLIST_TYPES = [
        ('medical', 'Medical Claims'),
        ('political', 'Political'),
        ('sensitive', 'Sensitive Topics'),
        ('profanity', 'Profanity'),
        ('other', 'Other'),
    ]
    
    phrase = models.CharField(max_length=200, unique=True)
    blacklist_type = models.CharField(max_length=20, choices=BLACKLIST_TYPES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['blacklist_type', 'phrase']
    
    def __str__(self):
        return f"{self.get_blacklist_type_display()}: {self.phrase}"
