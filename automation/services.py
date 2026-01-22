"""
Automation services for TikTok uploads with human-like behavior
"""
import random
import time
import json
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from playwright.sync_api import sync_playwright, Page, Browser
from accounts.models import TikTokAccount, UploadSchedule, UploadLog, AutomationSettings


class HumanBehaviorSimulator:
    """Simulate human-like behavior to avoid detection"""
    
    def __init__(self, settings: AutomationSettings = None):
        self.settings = settings or AutomationSettings.objects.first()
        if not self.settings:
            # Create default settings
            self.settings = AutomationSettings.objects.create()
    
    def random_delay(self, min_override: int = None, max_override: int = None) -> float:
        """Generate random delay in seconds"""
        if not self.settings.enable_human_behavior:
            return 0.5
        
        min_delay = min_override or self.settings.random_delay_min_seconds
        max_delay = max_override or self.settings.random_delay_max_seconds
        
        return random.uniform(min_delay, max_delay)
    
    def page_load_delay(self) -> float:
        """Delay after page load"""
        return random.uniform(
            self.settings.page_load_wait_min,
            self.settings.page_load_wait_max
        )
    
    def typing_delay(self) -> float:
        """Delay between keystrokes"""
        return random.uniform(0.05, 0.15)
    
    def mouse_movement_speed(self) -> float:
        """Random mouse movement speed"""
        if not self.settings.enable_mouse_movement:
            return 1.0
        
        return random.uniform(
            self.settings.mouse_speed_min,
            self.settings.mouse_speed_max
        )
    
    def should_take_break(self) -> bool:
        """Determine if system should take a random break"""
        if not self.settings.enable_random_breaks:
            return False
        
        return random.random() < self.settings.break_probability
    
    def is_overnight_hours(self) -> bool:
        """Check if current time is in overnight pause period"""
        if not self.settings.enable_overnight_pause:
            return False
        
        current_hour = timezone.now().hour
        
        if self.settings.overnight_start_hour > self.settings.overnight_end_hour:
            # Overnight period crosses midnight
            return current_hour >= self.settings.overnight_start_hour or current_hour < self.settings.overnight_end_hour
        else:
            return self.settings.overnight_start_hour <= current_hour < self.settings.overnight_end_hour


class TikTokUploader:
    """Handle TikTok video uploads using Playwright"""
    
    def __init__(self, account: TikTokAccount):
        self.account = account
        self.behavior = HumanBehaviorSimulator()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    def upload_video(self, upload_schedule: UploadSchedule) -> Tuple[bool, str]:
        """
        Upload video to TikTok
        
        Args:
            upload_schedule: UploadSchedule instance
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        log = UploadLog.objects.create(
            upload_schedule=upload_schedule,
            attempt_number=upload_schedule.retry_count + 1
        )
        
        try:
            # Check if account can upload
            if not self.account.can_upload_now:
                return False, "Account cannot upload at this time"
            
            # Check overnight hours
            if self.behavior.is_overnight_hours():
                return False, "Overnight pause period active"
            
            # Pre-upload delay (human behavior)
            time.sleep(self.behavior.random_delay())
            
            # Initialize browser
            self._init_browser()
            
            # Login or restore session
            if not self._ensure_logged_in():
                return False, "Failed to login"
            
            # Navigate to upload page
            if not self._navigate_to_upload():
                return False, "Failed to navigate to upload page"
            
            # Upload video file
            if not self._upload_file(upload_schedule.video.final_video.path):
                return False, "Failed to upload video file"
            
            # Add caption
            if not self._add_caption(upload_schedule.caption.text):
                return False, "Failed to add caption"
            
            # Add hashtags (already in caption)
            
            # Submit post
            if not self._submit_post():
                return False, "Failed to submit post"
            
            # Get video URL
            video_url = self._get_uploaded_video_url()
            
            # Update upload schedule
            upload_schedule.status = 'completed'
            upload_schedule.actual_upload_time = timezone.now()
            upload_schedule.tiktok_url = video_url
            upload_schedule.save()
            
            # Update account
            self.account.last_upload_time = timezone.now()
            self.account.total_uploads += 1
            self.account.save()
            
            # Update log
            log.success = True
            log.completed_at = timezone.now()
            log.save()
            
            return True, "Upload successful"
            
        except Exception as e:
            error_msg = str(e)
            
            # Update log
            log.success = False
            log.error_type = type(e).__name__
            log.error_details = error_msg
            log.completed_at = timezone.now()
            log.save()
            
            # Update upload schedule
            upload_schedule.status = 'failed'
            upload_schedule.error_message = error_msg
            upload_schedule.retry_count += 1
            upload_schedule.save()
            
            return False, error_msg
            
        finally:
            self._cleanup_browser()
    
    def _init_browser(self):
        """Initialize Playwright browser"""
        playwright = sync_playwright().start()
        
        self.browser = playwright.chromium.launch(
            headless=True,  # Set to False for debugging
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = context.new_page()
    
    def _ensure_logged_in(self) -> bool:
        """Ensure user is logged in, restore session if available"""
        try:
            # Try to restore session
            if self.account.session_is_valid and self.account.session_data:
                self._restore_session()
                
                # Verify session is still valid
                self.page.goto('https://www.tiktok.com/')
                time.sleep(self.behavior.page_load_delay())
                
                # Check if logged in (look for upload button or profile)
                if self.page.locator('[data-e2e="upload-icon"]').count() > 0:
                    return True
            
            # Session invalid, need manual login
            # For now, return False - admin must login manually first
            return False
            
        except Exception as e:
            from analytics.models import SystemLog
            SystemLog.objects.create(
                level='error',
                category='upload',
                message='Login failed',
                details={'error': str(e), 'account': self.account.username}
            )
            return False
    
    def _restore_session(self):
        """Restore browser session from saved cookies"""
        if self.account.session_data:
            cookies = self.account.session_data.get('cookies', [])
            for cookie in cookies:
                self.page.context.add_cookies([cookie])
    
    def _save_session(self):
        """Save browser session for future use"""
        cookies = self.page.context.cookies()
        
        self.account.session_data = {
            'cookies': cookies,
            'timestamp': timezone.now().isoformat()
        }
        self.account.session_last_updated = timezone.now()
        self.account.session_is_valid = True
        self.account.save()
    
    def _navigate_to_upload(self) -> bool:
        """Navigate to TikTok upload page"""
        try:
            self.page.goto('https://www.tiktok.com/upload')
            time.sleep(self.behavior.page_load_delay())
            return True
        except Exception:
            return False
    
    def _upload_file(self, video_path: str) -> bool:
        """Upload video file"""
        try:
            # Find file input
            file_input = self.page.locator('input[type="file"]')
            
            # Upload file
            file_input.set_input_files(video_path)
            
            # Wait for upload to complete (look for progress bar to disappear)
            time.sleep(5)  # Initial wait
            
            # Wait for processing
            max_wait = 120  # 2 minutes max
            waited = 0
            while waited < max_wait:
                # Check if upload is complete (this selector may need adjustment)
                if self.page.locator('[data-e2e="upload-complete"]').count() > 0:
                    break
                time.sleep(2)
                waited += 2
            
            return True
            
        except Exception:
            return False
    
    def _add_caption(self, caption: str) -> bool:
        """Add caption to video"""
        try:
            # Find caption textarea
            caption_input = self.page.locator('[data-e2e="caption-input"]').first
            
            # Type caption with human-like delays
            caption_input.click()
            time.sleep(0.5)
            
            # Type character by character
            for char in caption:
                caption_input.type(char)
                time.sleep(self.behavior.typing_delay())
            
            return True
            
        except Exception:
            return False
    
    def _submit_post(self) -> bool:
        """Submit the post"""
        try:
            # Find and click post button
            post_button = self.page.locator('[data-e2e="post-button"]').first
            
            # Human-like delay before clicking
            time.sleep(self.behavior.random_delay(2, 5))
            
            post_button.click()
            
            # Wait for post to complete
            time.sleep(10)
            
            return True
            
        except Exception:
            return False
    
    def _get_uploaded_video_url(self) -> str:
        """Get URL of uploaded video"""
        try:
            # This will need to be adjusted based on TikTok's actual response
            # For now, return empty string
            return ""
        except Exception:
            return ""
    
    def _cleanup_browser(self):
        """Close browser and cleanup"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
        except Exception:
            pass


class UploadScheduler:
    """Schedule video uploads intelligently"""
    
    def schedule_upload(
        self,
        account: TikTokAccount,
        video,
        caption,
        preferred_time: datetime = None
    ) -> Optional[UploadSchedule]:
        """
        Schedule a video upload
        
        Args:
            account: TikTokAccount instance
            video: Video instance
            caption: Caption instance
            preferred_time: Preferred upload time (optional)
        
        Returns:
            UploadSchedule instance or None
        """
        # Calculate optimal upload time
        scheduled_time = self._calculate_optimal_time(account, preferred_time)
        
        if not scheduled_time:
            return None
        
        # Generate random pre-upload delay
        pre_delay = random.randint(30, 180)
        
        # Create schedule
        schedule = UploadSchedule.objects.create(
            account=account,
            video=video,
            caption=caption,
            scheduled_time=scheduled_time,
            pre_upload_delay=pre_delay
        )
        
        return schedule
    
    def _calculate_optimal_time(
        self,
        account: TikTokAccount,
        preferred_time: datetime = None
    ) -> Optional[datetime]:
        """Calculate optimal upload time"""
        if preferred_time:
            base_time = preferred_time
        else:
            # Default to next available slot
            base_time = timezone.now() + timedelta(hours=account.min_hours_between_posts)
        
        # Add random variation (±30 minutes)
        variation = timedelta(minutes=random.randint(-30, 30))
        scheduled_time = base_time + variation
        
        # Ensure not in overnight hours
        behavior = HumanBehaviorSimulator()
        settings = AutomationSettings.objects.first()
        
        if settings and settings.enable_overnight_pause:
            hour = scheduled_time.hour
            if settings.overnight_start_hour <= hour or hour < settings.overnight_end_hour:
                # Move to next morning
                scheduled_time = scheduled_time.replace(
                    hour=settings.overnight_end_hour,
                    minute=random.randint(0, 59)
                )
        
        return scheduled_time
