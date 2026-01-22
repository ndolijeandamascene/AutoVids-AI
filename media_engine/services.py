"""
Media generation services for video creation
"""
import os
import random
from typing import Optional, List, Tuple
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from .models import Video, BackgroundVideo, VoiceProfile, SubtitleSegment
from content.models import Fact


class VoiceGenerator:
    """Text-to-Speech service"""
    
    def __init__(self, provider: str = None):
        self.provider = provider or getattr(settings, 'DEFAULT_TTS_PROVIDER', 'elevenlabs')
    
    def generate_audio(self, text: str, voice_profile: VoiceProfile, output_path: str) -> str:
        """
        Generate audio from text
        
        Args:
            text: Text to convert to speech
            voice_profile: VoiceProfile to use
            output_path: Path to save audio file
        
        Returns:
            Path to generated audio file
        """
        if self.provider == 'elevenlabs':
            return self._generate_elevenlabs(text, voice_profile, output_path)
        elif self.provider == 'gtts':
            return self._generate_gtts(text, voice_profile, output_path)
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")
    
    def _generate_elevenlabs(self, text: str, voice_profile: VoiceProfile, output_path: str) -> str:
        """Generate audio using ElevenLabs"""
        try:
            from elevenlabs import generate, save, Voice, VoiceSettings
            
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=voice_profile.voice_id,
                    settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.5,
                        use_speaker_boost=True
                    )
                ),
                model="eleven_multilingual_v2"
            )
            
            save(audio, output_path)
            return output_path
            
        except Exception as e:
            raise Exception(f"ElevenLabs TTS error: {str(e)}")
    
    def _generate_gtts(self, text: str, voice_profile: VoiceProfile, output_path: str) -> str:
        """Generate audio using Google TTS"""
        try:
            from gtts import gTTS
            
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            
            # Apply speed modification if needed
            if voice_profile.speed_multiplier != 1.0:
                self._adjust_audio_speed(output_path, voice_profile.speed_multiplier)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"gTTS error: {str(e)}")
    
    def _adjust_audio_speed(self, audio_path: str, speed: float):
        """Adjust audio speed using moviepy"""
        from moviepy.editor import AudioFileClip
        
        audio = AudioFileClip(audio_path)
        audio = audio.fx(lambda clip: clip.speedx(speed))
        audio.write_audiofile(audio_path, verbose=False, logger=None)
        audio.close()
    
    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        from moviepy.editor import AudioFileClip
        
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        audio.close()
        return duration


class SubtitleGenerator:
    """Generate subtitles for videos"""
    
    def generate_subtitles(self, text: str, audio_duration: float, video: Video) -> List[SubtitleSegment]:
        """
        Generate subtitle segments
        
        Args:
            text: Full text to subtitle
            audio_duration: Duration of audio in seconds
            video: Video instance
        
        Returns:
            List of SubtitleSegment instances
        """
        # Split text into words
        words = text.split()
        
        # Calculate timing (simple word-based distribution)
        words_per_segment = 3  # Show 3 words at a time
        segments = []
        
        time_per_word = audio_duration / len(words)
        current_time = 0
        
        for i in range(0, len(words), words_per_segment):
            segment_words = words[i:i + words_per_segment]
            segment_text = ' '.join(segment_words)
            
            start_time = current_time
            end_time = current_time + (len(segment_words) * time_per_word)
            
            segment = SubtitleSegment.objects.create(
                video=video,
                text=segment_text,
                start_time=start_time,
                end_time=end_time,
                sequence=len(segments)
            )
            
            segments.append(segment)
            current_time = end_time
        
        return segments
    
    def create_srt_file(self, segments: List[SubtitleSegment], output_path: str) -> str:
        """Create SRT subtitle file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{self._format_time(segment.start_time)} --> {self._format_time(segment.end_time)}\n")
                f.write(f"{segment.text}\n\n")
        
        return output_path
    
    def _format_time(self, seconds: float) -> str:
        """Format time for SRT format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class VideoComposer:
    """Compose final video from components"""
    
    def compose_video(self, video: Video) -> str:
        """
        Compose final video
        
        Args:
            video: Video instance with all components
        
        Returns:
            Path to final video file
        """
        from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
        from moviepy.video.fx import resize
        
        try:
            # Load background video
            background = VideoFileClip(video.background_video.file.path)
            
            # Load audio
            audio = AudioFileClip(video.audio_file.path)
            audio_duration = audio.duration
            
            # Trim or loop background to match audio duration
            if background.duration < audio_duration:
                # Loop background if too short
                loops = int(audio_duration / background.duration) + 1
                background = background.loop(n=loops)
            
            background = background.subclip(0, audio_duration)
            
            # Resize to TikTok format (1080x1920)
            background = background.fx(resize, height=1920)
            if background.w > 1080:
                background = background.crop(
                    x_center=background.w/2,
                    width=1080,
                    height=1920
                )
            
            # Add audio
            background = background.set_audio(audio)
            
            # Add subtitles
            subtitle_clips = self._create_subtitle_clips(video)
            
            # Composite everything
            final = CompositeVideoClip([background] + subtitle_clips)
            
            # Output path
            output_path = os.path.join(
                settings.MEDIA_ROOT,
                'videos',
                'generated',
                f'video_{video.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.mp4'
            )
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write final video
            final.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                verbose=False,
                logger=None
            )
            
            # Clean up
            background.close()
            audio.close()
            final.close()
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Video composition error: {str(e)}")
    
    def _create_subtitle_clips(self, video: Video) -> List:
        """Create subtitle text clips"""
        from moviepy.editor import TextClip
        
        clips = []
        segments = video.subtitle_segments.all().order_by('sequence')
        
        for segment in segments:
            txt_clip = TextClip(
                segment.text,
                fontsize=video.subtitle_font_size,
                color=video.subtitle_color,
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(1000, None)
            )
            
            # Position subtitle
            if video.subtitle_position == 'center':
                txt_clip = txt_clip.set_position('center')
            elif video.subtitle_position == 'bottom':
                txt_clip = txt_clip.set_position(('center', 1600))
            else:
                txt_clip = txt_clip.set_position(('center', 'center'))
            
            txt_clip = txt_clip.set_start(segment.start_time).set_duration(
                segment.end_time - segment.start_time
            )
            
            clips.append(txt_clip)
        
        return clips


class BackgroundSelector:
    """Select appropriate background videos"""
    
    def select_background(self, category_name: str = None) -> Optional[BackgroundVideo]:
        """
        Select a background video
        
        Args:
            category_name: Optional category to match background type
        
        Returns:
            BackgroundVideo instance
        """
        # Get active backgrounds
        backgrounds = BackgroundVideo.objects.filter(is_active=True)
        
        if not backgrounds.exists():
            return None
        
        # Get last used background to avoid repetition
        last_video = Video.objects.filter(background_video__isnull=False).order_by('-created_at').first()
        last_bg = last_video.background_video if last_video else None
        
        # Exclude last used
        if last_bg:
            backgrounds = backgrounds.exclude(id=last_bg.id)
        
        # Order by least used
        backgrounds = backgrounds.order_by('usage_count', 'last_used')
        
        # Select from top 3 least used
        top_backgrounds = list(backgrounds[:3])
        
        if not top_backgrounds:
            # If all filtered out, use any
            top_backgrounds = list(BackgroundVideo.objects.filter(is_active=True)[:3])
        
        return random.choice(top_backgrounds) if top_backgrounds else None


class VoiceSelector:
    """Select appropriate voice profiles"""
    
    def select_voice(self) -> Optional[VoiceProfile]:
        """
        Select a voice profile with variation
        
        Returns:
            VoiceProfile instance
        """
        # Get active voices
        voices = VoiceProfile.objects.filter(is_active=True)
        
        if not voices.exists():
            return None
        
        # Get last used voice to ensure variation
        last_video = Video.objects.filter(voice_profile__isnull=False).order_by('-created_at').first()
        last_voice = last_video.voice_profile if last_video else None
        
        # Try to alternate gender
        if last_voice:
            opposite_gender = 'female' if last_voice.gender == 'male' else 'male'
            opposite_voices = voices.filter(gender=opposite_gender)
            
            if opposite_voices.exists():
                voices = opposite_voices
        
        # Order by least used
        voices = voices.order_by('usage_count', 'last_used')
        
        # Select from top 2 least used
        top_voices = list(voices[:2])
        
        return random.choice(top_voices) if top_voices else None
