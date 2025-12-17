from openai import OpenAI
import os
import requests
import tempfile
from app.config import Config

def generate_linkedin_post(transcript, video_title=None):
    """
    Generate LinkedIn post content using OpenAI with proper title, description, and tags
    """
    try:
        if not Config.OPENAI_API_KEY:
            return generate_fallback_content(transcript, video_title)
        
        # Initialize OpenAI client
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Generate LinkedIn post content
        linkedin_post = generate_linkedin_content(client, transcript, video_title)
        
        # Generate image if content is substantial
        image_path = None
        if len(transcript) > 200:
            try:
                image_path = generate_post_image(client, video_title, transcript[:500])
                if not image_path or not os.path.exists(image_path):
                    image_path = None
            except Exception as img_error:
                print(f"Image generation failed: {img_error}")
                image_path = None
        
        # Return structured result
        return {
            'post': linkedin_post,
            'content': linkedin_post,
            'image_url': image_path  # Actually image_path now
        }
        
    except Exception as e:
        print(f"OpenAI content generation error: {str(e)}")
        return generate_fallback_content(transcript, video_title)

def generate_linkedin_content(client, transcript, video_title):
    """Generate structured LinkedIn content using OpenAI"""
    
    prompt = f"""Analyze this video transcript and create a professional LinkedIn post:

VIDEO TITLE: {video_title or "Video Content"}
TRANSCRIPT: {transcript[:3000]}

Create a natural LinkedIn post that:
- Starts with an engaging hook related to the actual video content
- Summarizes key insights from the transcript (not generic tech content)
- Uses 3-4 bullet points for main takeaways
- Includes 5-7 relevant hashtags based on the actual content
- Ends with an engaging question
- Sounds natural and human-written
- NEVER mentions AI, automation, or generated content
- Focus on the actual video topic and insights

Write as if you watched the video and are sharing genuine insights with your professional network."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional creating LinkedIn content. Write natural, engaging posts based on video content. Never mention AI or automation. Focus on genuine insights from the transcript."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )
    
    # Just return the raw content
    return response.choices[0].message.content.strip()

def generate_post_image(client, title, transcript_sample):
    """Generate and save image locally"""
    import os
    import requests
    from datetime import datetime
    
    # Create images directory
    images_dir = Config.IMAGES_FOLDER
    os.makedirs(images_dir, exist_ok=True)
    
    # Create image prompt based on actual content
    image_prompt = f"""Professional business illustration about: {title}
    
Based on this content: {transcript_sample[:300]}

Style: Clean, modern, professional business illustration
Colors: Professional blue, white, light gray gradient
Elements: Abstract geometric shapes, business icons related to the topic
Quality: High-quality, suitable for social media (Instagram, Facebook, LinkedIn)
No text, words, or logos in the image - visual elements only
Corporate aesthetic, engaging but professional
No platform-specific branding or logos"""
    
    print(f"🎨 Image prompt: {image_prompt[:150]}...")
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        
        # Download and save image locally
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"linkedin_post_{timestamp}.png"
        local_path = os.path.join(images_dir, filename)
        
        print(f"📥 Downloading image from DALL-E to: {local_path}")
        
        img_response = requests.get(image_url, stream=True)
        if img_response.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file was created
            if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
                return local_path
            else:
                print(f"Failed to create image file: {local_path}")
                return None
        else:
            print(f"❌ Failed to download image: HTTP {img_response.status_code}")
            return None
    except Exception as e:
        print(f"DALL-E error: {str(e)}")
        raise e


def generate_fallback_content(transcript, video_title):
    """Fallback content when OpenAI is not available - create content based on actual transcript"""
    
    # Extract some key words from transcript for better content
    words = transcript.lower().split()
    common_topics = {
        'business': ['business', 'company', 'revenue', 'profit', 'strategy', 'market'],
        'technology': ['tech', 'software', 'app', 'digital', 'system', 'platform'],
        'lifestyle': ['life', 'tips', 'hack', 'easy', 'simple', 'quick'],
        'education': ['learn', 'teaching', 'education', 'training', 'skill'],
        'health': ['health', 'fitness', 'wellness', 'exercise', 'body']
    }
    
    detected_topics = []
    for topic, keywords in common_topics.items():
        if any(keyword in words for keyword in keywords):
            detected_topics.append(topic)
    
    # Create hashtags based on detected topics
    hashtag_map = {
        'business': '#Business #Entrepreneurship #Strategy #Leadership',
        'technology': '#Technology #Innovation #DigitalTransformation #Tech',
        'lifestyle': '#Lifestyle #Tips #LifeHacks #Productivity',
        'education': '#Learning #Education #Skills #Development',
        'health': '#Health #Wellness #Fitness #Lifestyle'
    }
    
    hashtags = []
    for topic in detected_topics[:2]:  # Max 2 topic groups
        hashtags.extend(hashtag_map.get(topic, '').split())
    
    if not hashtags:
        hashtags = ['#Insights', '#Professional', '#Learning', '#Growth']
    
    hashtags_str = ' '.join(hashtags[:6])  # Max 6 hashtags
    
    post_content = f"""Interesting insights from: "{video_title or 'Recent Analysis'}"

Key takeaways that caught my attention:
• {transcript[:100].strip()}...
• Practical applications worth considering
• Valuable perspective on the topic

The discussion brings up important points that many professionals can relate to.

What's your experience with this topic?

{hashtags_str}"""
    
    return {
        'post': post_content,
        'content': post_content,
        'image_url': None
    }
