"""
AI-powered content generation services
"""
import hashlib
import random
from typing import Dict, List, Optional
from django.conf import settings
from django.utils import timezone
from .models import Fact, HookTemplate, ContentCategory, Caption, ContentBlacklist


class AIContentGenerator:
    """Main AI content generation service"""
    
    def __init__(self, provider: str = None):
        self.provider = provider or getattr(settings, 'DEFAULT_AI_PROVIDER', 'openai')
    
    def generate_fact(self, category: ContentCategory, max_retries: int = 3) -> Optional[Fact]:
        """
        Generate a new fact for the given category
        
        Args:
            category: ContentCategory instance
            max_retries: Number of retry attempts if generation fails
        
        Returns:
            Fact instance or None if generation fails
        """
        for attempt in range(max_retries):
            try:
                # Generate fact content using AI
                fact_content = self._call_ai_for_fact(category)
                
                # Check for blacklisted content
                if self._contains_blacklisted_content(fact_content):
                    continue
                
                # Check for duplicates
                content_hash = self._generate_content_hash(fact_content)
                if Fact.objects.filter(content_hash=content_hash).exists():
                    continue
                
                # Select appropriate hook
                hook = self._select_hook()
                full_script = self._combine_hook_and_fact(hook, fact_content)
                
                # Create fact
                fact = Fact.objects.create(
                    category=category,
                    content=fact_content,
                    hook_used=hook,
                    full_script=full_script,
                    ai_provider=self.provider,
                    generation_prompt=self._get_generation_prompt(category),
                    content_hash=content_hash,
                    similarity_checked=True,
                    is_approved=True,  # Auto-approve for now
                    quality_score=self._calculate_quality_score(fact_content)
                )
                
                # Mark hook as used
                if hook:
                    hook.mark_used()
                
                return fact
                
            except Exception as e:
                from analytics.models import SystemLog
                SystemLog.objects.create(
                    level='error',
                    category='content_generation',
                    message=f'Fact generation failed (attempt {attempt + 1})',
                    details={'error': str(e), 'category': category.name}
                )
                
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def _call_ai_for_fact(self, category: ContentCategory) -> str:
        """Call AI API to generate fact content"""
        prompt = self._get_generation_prompt(category)
        
        if self.provider == 'openai':
            return self._call_openai(prompt)
        elif self.provider == 'anthropic':
            return self._call_anthropic(prompt)
        elif self.provider == 'google':
            return self._call_google_ai(prompt)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    def _get_generation_prompt(self, category: ContentCategory) -> str:
        """Generate prompt for AI"""
        return f"""Generate a surprising and engaging fact about {category.name}.

Requirements:
- 1-2 sentences maximum
- Simple English only
- High curiosity factor
- Scientifically accurate
- No medical claims
- No political content
- No sensitive topics
- Must be safe for all audiences

Category: {category.name}
Description: {category.description}

Generate only the fact, no additional text."""
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a fact generator that creates surprising, engaging, and accurate facts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            
            message = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text.strip()
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _call_google_ai(self, prompt: str) -> str:
        """Call Google Gemini API"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Google AI API error: {str(e)}")
    
    def _select_hook(self) -> Optional[HookTemplate]:
        """Select the best hook template to use"""
        # Get active hooks, ordered by least recently used
        hooks = HookTemplate.objects.filter(is_active=True).order_by('usage_count', 'last_used')
        
        if not hooks.exists():
            return None
        
        # Get the last used hook type to avoid repetition
        last_fact = Fact.objects.filter(hook_used__isnull=False).order_by('-created_at').first()
        last_hook_type = last_fact.hook_used.hook_type if last_fact and last_fact.hook_used else None
        
        # Try to select a different hook type
        if last_hook_type:
            different_hooks = hooks.exclude(hook_type=last_hook_type)
            if different_hooks.exists():
                hooks = different_hooks
        
        # Select from top 3 least used
        top_hooks = list(hooks[:3])
        return random.choice(top_hooks) if top_hooks else None
    
    def _combine_hook_and_fact(self, hook: Optional[HookTemplate], fact: str) -> str:
        """Combine hook template with fact"""
        if not hook:
            return fact
        
        return hook.template.replace('{fact}', fact)
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for duplicate detection"""
        return hashlib.sha256(content.lower().encode()).hexdigest()
    
    def _contains_blacklisted_content(self, content: str) -> bool:
        """Check if content contains blacklisted phrases"""
        content_lower = content.lower()
        blacklisted = ContentBlacklist.objects.filter(is_active=True)
        
        for item in blacklisted:
            if item.phrase.lower() in content_lower:
                return True
        
        return False
    
    def _calculate_quality_score(self, content: str) -> int:
        """Calculate quality score for content"""
        score = 50  # Base score
        
        # Length check (prefer 1-2 sentences)
        word_count = len(content.split())
        if 15 <= word_count <= 40:
            score += 20
        elif word_count < 10 or word_count > 60:
            score -= 20
        
        # Sentence count
        sentence_count = content.count('.') + content.count('!') + content.count('?')
        if sentence_count <= 2:
            score += 15
        
        # Engagement words
        engagement_words = ['surprising', 'amazing', 'incredible', 'never', 'always', 'only']
        for word in engagement_words:
            if word in content.lower():
                score += 5
        
        return max(0, min(100, score))


class CaptionGenerator:
    """Generate TikTok captions"""
    
    def generate_caption(self, fact: Fact, style: str = 'engaging') -> Caption:
        """Generate caption for a fact"""
        # Generate caption text
        caption_text = self._generate_caption_text(fact, style)
        
        # Generate hashtags
        hashtags = self._generate_hashtags(fact)
        
        # Create caption
        caption = Caption.objects.create(
            fact=fact,
            text=caption_text,
            hashtags=hashtags,
            style=style,
            emoji_count=caption_text.count('🔥') + caption_text.count('🤯') + caption_text.count('💡')
        )
        
        return caption
    
    def _generate_caption_text(self, fact: Fact, style: str) -> str:
        """Generate caption text"""
        emojis = ['🔥', '🤯', '💡', '✨', '🧠', '👀']
        selected_emojis = random.sample(emojis, 3)
        
        templates = [
            f"{selected_emojis[0]} Mind-blowing fact alert! {selected_emojis[1]}\n\n{fact.content}\n\n{selected_emojis[2]} Follow for more!",
            f"Did you know? {selected_emojis[0]}\n\n{fact.content}\n\nDrop a {selected_emojis[1]} if this surprised you!",
            f"{selected_emojis[0]} Here's something you probably didn't know...\n\n{fact.content}\n\n{selected_emojis[2]} Tag someone who needs to see this!",
        ]
        
        return random.choice(templates)
    
    def _generate_hashtags(self, fact: Fact) -> str:
        """Generate relevant hashtags"""
        base_hashtags = ['#didyouknow', '#facts', '#mindblown', '#interesting', '#fyp', '#foryou', '#viral']
        
        # Add category-specific hashtags
        category_hashtags = {
            'Psychology': ['#psychology', '#mindtricks', '#brain'],
            'Human Body': ['#humanbody', '#science', '#biology'],
            'World Facts': ['#worldfacts', '#geography', '#history'],
            'Tech Facts': ['#technology', '#tech', '#innovation'],
        }
        
        category_tags = category_hashtags.get(fact.category.name, [])
        
        # Combine and limit to 10 hashtags
        all_tags = base_hashtags + category_tags
        selected_tags = random.sample(all_tags, min(10, len(all_tags)))
        
        return ' '.join(selected_tags)
