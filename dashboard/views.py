from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from content.models import Fact, ContentCategory, HookTemplate
from media_engine.models import Video
from accounts.models import TikTokAccount, UploadSchedule
from analytics.models import VideoPerformance, DailyAnalytics, SystemLog


@login_required
def dashboard(request):
    """Main dashboard view"""
    
    # Get date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Content Statistics
    total_facts = Fact.objects.count()
    approved_facts = Fact.objects.filter(is_approved=True).count()
    unused_facts = Fact.objects.filter(is_used=False, is_approved=True).count()
    
    # Video Statistics
    total_videos = Video.objects.count()
    completed_videos = Video.objects.filter(status='completed').count()
    pending_videos = Video.objects.filter(status='pending').count()
    generating_videos = Video.objects.filter(status='generating').count()
    
    # Account Statistics
    total_accounts = TikTokAccount.objects.count()
    active_accounts = TikTokAccount.objects.filter(status='active', is_automation_enabled=True).count()
    
    # Upload Statistics
    total_uploads = UploadSchedule.objects.filter(status='completed').count()
    pending_uploads = UploadSchedule.objects.filter(status='scheduled').count()
    failed_uploads = UploadSchedule.objects.filter(status='failed').count()
    
    # Performance Metrics
    total_views = VideoPerformance.objects.aggregate(Sum('views'))['views__sum'] or 0
    total_likes = VideoPerformance.objects.aggregate(Sum('likes'))['likes__sum'] or 0
    avg_engagement = VideoPerformance.objects.aggregate(Avg('engagement_rate'))['engagement_rate__avg'] or 0
    
    # Recent Activity
    recent_videos = Video.objects.filter(status='completed').order_by('-created_at')[:5]
    recent_uploads = UploadSchedule.objects.filter(status='completed').order_by('-actual_upload_time')[:5]
    recent_logs = SystemLog.objects.filter(level__in=['warning', 'error', 'critical']).order_by('-created_at')[:10]
    
    # Upcoming Schedules
    upcoming_uploads = UploadSchedule.objects.filter(
        status='scheduled',
        scheduled_time__gte=timezone.now()
    ).order_by('scheduled_time')[:10]
    
    # Category Performance
    categories = ContentCategory.objects.filter(is_active=True).annotate(
        fact_count=Count('facts')
    )
    
    context = {
        # Stats
        'total_facts': total_facts,
        'approved_facts': approved_facts,
        'unused_facts': unused_facts,
        'total_videos': total_videos,
        'completed_videos': completed_videos,
        'pending_videos': pending_videos,
        'generating_videos': generating_videos,
        'total_accounts': total_accounts,
        'active_accounts': active_accounts,
        'total_uploads': total_uploads,
        'pending_uploads': pending_uploads,
        'failed_uploads': failed_uploads,
        'total_views': total_views,
        'total_likes': total_likes,
        'avg_engagement': avg_engagement,
        
        # Recent Activity
        'recent_videos': recent_videos,
        'recent_uploads': recent_uploads,
        'recent_logs': recent_logs,
        'upcoming_uploads': upcoming_uploads,
        'categories': categories,
    }
    
    return render(request, 'dashboard/index.html', context)


@login_required
def content_management(request):
    """Content management view"""
    facts = Fact.objects.select_related('category', 'hook_used').order_by('-created_at')[:50]
    categories = ContentCategory.objects.filter(is_active=True)
    hooks = HookTemplate.objects.filter(is_active=True).order_by('usage_count')
    
    context = {
        'facts': facts,
        'categories': categories,
        'hooks': hooks,
    }
    
    return render(request, 'dashboard/content.html', context)


@login_required
def video_library(request):
    """Video library view"""
    videos = Video.objects.select_related('fact', 'background_video', 'voice_profile').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        videos = videos.filter(status=status_filter)
    
    context = {
        'videos': videos,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/videos.html', context)


@login_required
def accounts_view(request):
    """Accounts management view"""
    accounts = TikTokAccount.objects.all().order_by('-created_at')
    
    context = {
        'accounts': accounts,
    }
    
    return render(request, 'dashboard/accounts.html', context)


@login_required
def analytics_view(request):
    """Analytics dashboard"""
    # Get date range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now().date() - timedelta(days=days)
    
    # Daily analytics
    daily_stats = DailyAnalytics.objects.filter(
        date__gte=start_date
    ).order_by('date')
    
    # Top performing videos
    top_videos = VideoPerformance.objects.select_related(
        'upload_schedule__video__fact'
    ).order_by('-views')[:10]
    
    # Category insights
    from analytics.models import ContentPerformanceInsight
    category_insights = ContentPerformanceInsight.objects.all().order_by('-avg_views')
    
    context = {
        'daily_stats': daily_stats,
        'top_videos': top_videos,
        'category_insights': category_insights,
        'days': days,
    }
    
    return render(request, 'dashboard/analytics.html', context)


@login_required
def system_logs(request):
    """System logs view"""
    level_filter = request.GET.get('level')
    category_filter = request.GET.get('category')
    
    logs = SystemLog.objects.all()
    
    if level_filter:
        logs = logs.filter(level=level_filter)
    if category_filter:
        logs = logs.filter(category=category_filter)
    
    logs = logs.order_by('-created_at')[:100]
    
    context = {
        'logs': logs,
        'level_filter': level_filter,
        'category_filter': category_filter,
    }
    
    return render(request, 'dashboard/logs.html', context)
