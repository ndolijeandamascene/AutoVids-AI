"""
Celery tasks for automated content generation and uploads
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta


@shared_task
def generate_daily_content():
    """Generate content for the day"""
    from content.models import ContentCategory, Fact
    from content.services import AIContentGenerator, CaptionGenerator
    from analytics.models import SystemLog
    
    try:
        generator = AIContentGenerator()
        caption_gen = CaptionGenerator()
        
        # Get active categories
        categories = ContentCategory.objects.filter(is_active=True)
        
        facts_generated = 0
        
        for category in categories:
            # Generate 2-3 facts per category
            for _ in range(2):
                fact = generator.generate_fact(category)
                
                if fact:
                    # Generate caption
                    caption_gen.generate_caption(fact)
                    facts_generated += 1
        
        SystemLog.objects.create(
            level='info',
            category='content_generation',
            message=f'Daily content generation completed',
            details={'facts_generated': facts_generated}
        )
        
        return f"Generated {facts_generated} facts"
        
    except Exception as e:
        SystemLog.objects.create(
            level='error',
            category='content_generation',
            message='Daily content generation failed',
            details={'error': str(e)}
        )
        raise


@shared_task
def create_video_from_fact(fact_id: int):
    """Create video from a fact"""
    from content.models import Fact
    from media_engine.models import Video
    from media_engine.services import (
        VoiceGenerator, SubtitleGenerator, VideoComposer,
        BackgroundSelector, VoiceSelector
    )
    from analytics.models import SystemLog
    from django.core.files import File
    import os
    
    try:
        fact = Fact.objects.get(id=fact_id)
        
        # Select background and voice
        bg_selector = BackgroundSelector()
        voice_selector = VoiceSelector()
        
        background = bg_selector.select_background(fact.category.name)
        voice = voice_selector.select_voice()
        
        if not background or not voice:
            raise Exception("No background or voice available")
        
        # Create video record
        video = Video.objects.create(
            fact=fact,
            background_video=background,
            voice_profile=voice,
            status='generating',
            generation_started=timezone.now()
        )
        
        # Generate audio
        voice_gen = VoiceGenerator()
        audio_path = os.path.join('/tmp', f'audio_{video.id}.mp3')
        
        voice_gen.generate_audio(fact.full_script, voice, audio_path)
        
        # Save audio file
        with open(audio_path, 'rb') as f:
            video.audio_file.save(f'audio_{video.id}.mp3', File(f))
        
        # Get audio duration
        audio_duration = voice_gen.get_audio_duration(audio_path)
        video.duration = audio_duration
        video.save()
        
        # Generate subtitles
        subtitle_gen = SubtitleGenerator()
        segments = subtitle_gen.generate_subtitles(fact.full_script, audio_duration, video)
        
        # Create SRT file
        srt_path = os.path.join('/tmp', f'subtitles_{video.id}.srt')
        subtitle_gen.create_srt_file(segments, srt_path)
        
        with open(srt_path, 'rb') as f:
            video.subtitle_file.save(f'subtitles_{video.id}.srt', File(f))
        
        # Compose final video
        composer = VideoComposer()
        final_video_path = composer.compose_video(video)
        
        # Save final video
        with open(final_video_path, 'rb') as f:
            video.final_video.save(f'video_{video.id}.mp4', File(f))
        
        # Update video status
        video.status = 'completed'
        video.generation_completed = timezone.now()
        video.file_size = os.path.getsize(final_video_path)
        video.save()
        
        # Mark background and voice as used
        background.mark_used()
        voice.mark_used()
        
        # Mark fact as used
        fact.is_used = True
        fact.used_in_video = video
        fact.save()
        
        SystemLog.objects.create(
            level='info',
            category='video_creation',
            message=f'Video created successfully',
            details={'video_id': video.id, 'fact_id': fact.id},
            video=video
        )
        
        return f"Video {video.id} created successfully"
        
    except Exception as e:
        if 'video' in locals():
            video.status = 'failed'
            video.error_message = str(e)
            video.save()
        
        SystemLog.objects.create(
            level='error',
            category='video_creation',
            message='Video creation failed',
            details={'error': str(e), 'fact_id': fact_id}
        )
        raise


@shared_task
def process_scheduled_uploads():
    """Process pending upload schedules"""
    from accounts.models import UploadSchedule, TikTokAccount
    from automation.services import TikTokUploader
    from analytics.models import SystemLog
    
    try:
        # Get uploads ready to process
        now = timezone.now()
        
        pending_uploads = UploadSchedule.objects.filter(
            status='scheduled',
            scheduled_time__lte=now
        ).select_related('account', 'video', 'caption')
        
        processed = 0
        successful = 0
        
        for upload in pending_uploads:
            # Check if account is ready
            if not upload.account.can_upload_now:
                continue
            
            # Check account risk score
            upload.account.calculate_risk_score()
            if upload.account.risk_score > 70:
                SystemLog.objects.create(
                    level='warning',
                    category='upload',
                    message='Upload skipped due to high risk score',
                    details={'account': upload.account.username, 'risk_score': upload.account.risk_score},
                    account=upload.account
                )
                continue
            
            # Process upload
            upload.status = 'uploading'
            upload.upload_started = timezone.now()
            upload.save()
            
            uploader = TikTokUploader(upload.account)
            success, message = uploader.upload_video(upload)
            
            processed += 1
            if success:
                successful += 1
        
        SystemLog.objects.create(
            level='info',
            category='upload',
            message=f'Upload processing completed',
            details={'processed': processed, 'successful': successful}
        )
        
        return f"Processed {processed} uploads, {successful} successful"
        
    except Exception as e:
        SystemLog.objects.create(
            level='error',
            category='upload',
            message='Upload processing failed',
            details={'error': str(e)}
        )
        raise


@shared_task
def schedule_daily_uploads():
    """Schedule uploads for active accounts"""
    from accounts.models import TikTokAccount
    from media_engine.models import Video
    from content.models import Caption
    from automation.services import UploadScheduler
    from analytics.models import SystemLog
    
    try:
        # Get active accounts
        accounts = TikTokAccount.objects.filter(
            status='active',
            is_automation_enabled=True
        )
        
        scheduler = UploadScheduler()
        scheduled_count = 0
        
        for account in accounts:
            # Check if account can upload today
            if not account.can_upload_now:
                continue
            
            # Get available videos
            available_videos = Video.objects.filter(
                status='completed',
                fact__is_used=True,
                upload_schedules__isnull=True
            ).first()
            
            if not available_videos:
                continue
            
            # Get caption
            caption = available_videos.fact.captions.filter(is_used=False).first()
            
            if not caption:
                continue
            
            # Schedule upload
            schedule = scheduler.schedule_upload(account, available_videos, caption)
            
            if schedule:
                scheduled_count += 1
                caption.is_used = True
                caption.save()
        
        SystemLog.objects.create(
            level='info',
            category='automation',
            message=f'Daily upload scheduling completed',
            details={'scheduled': scheduled_count}
        )
        
        return f"Scheduled {scheduled_count} uploads"
        
    except Exception as e:
        SystemLog.objects.create(
            level='error',
            category='automation',
            message='Upload scheduling failed',
            details={'error': str(e)}
        )
        raise


@shared_task
def sync_video_analytics():
    """Sync analytics from TikTok (placeholder for future implementation)"""
    from analytics.models import SystemLog
    
    # This would integrate with TikTok's API to fetch video performance
    # For now, it's a placeholder
    
    SystemLog.objects.create(
        level='info',
        category='analytics',
        message='Analytics sync completed (placeholder)',
        details={}
    )
    
    return "Analytics sync completed"


@shared_task
def cleanup_old_files():
    """Clean up old temporary files"""
    import os
    import shutil
    from django.conf import settings
    from analytics.models import SystemLog
    
    try:
        # Clean up temp audio files
        temp_dirs = [
            os.path.join(settings.MEDIA_ROOT, 'audio', 'temp'),
            os.path.join(settings.MEDIA_ROOT, 'backgrounds', 'temp'),
        ]
        
        cleaned = 0
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        # Delete files older than 24 hours
                        if os.path.getmtime(file_path) < (timezone.now().timestamp() - 86400):
                            os.remove(file_path)
                            cleaned += 1
        
        SystemLog.objects.create(
            level='info',
            category='system',
            message=f'File cleanup completed',
            details={'files_cleaned': cleaned}
        )
        
        return f"Cleaned {cleaned} files"
        
    except Exception as e:
        SystemLog.objects.create(
            level='error',
            category='system',
            message='File cleanup failed',
            details={'error': str(e)}
        )
        raise
