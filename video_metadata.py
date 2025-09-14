"""
Utility module for fetching YouTube video metadata including publication date.
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from dataclasses import dataclass


@dataclass
class VideoMetadata:
    """Container for YouTube video metadata."""
    video_id: str
    title: str
    publish_date: datetime
    channel_name: str
    description: str
    duration: Optional[str] = None
    view_count: Optional[int] = None


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from YouTube URL or return if already an ID."""
    # If it's already just an ID (11 characters, alphanumeric + _ -)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # Extract from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    raise ValueError(f"Could not extract video ID from: {url_or_id}")


def get_video_metadata(video_id: str) -> VideoMetadata:
    """
    Fetch YouTube video metadata using yt-dlp approach.
    Falls back to web scraping if needed.
    """
    try:
        # Try using yt-dlp first (more reliable)
        return _get_metadata_ytdlp(video_id)
    except Exception as e:
        print(f"yt-dlp failed: {e}, trying web scraping...")
        try:
            return _get_metadata_web_scraping(video_id)
        except Exception as e2:
            print(f"Web scraping also failed: {e2}")
            raise Exception(f"Could not fetch metadata for video {video_id}: {e2}")


def _get_metadata_ytdlp(video_id: str) -> VideoMetadata:
    """Fetch metadata using yt-dlp."""
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            
            # Parse upload date
            upload_date_str = info.get('upload_date', '')
            if upload_date_str:
                publish_date = datetime.strptime(upload_date_str, '%Y%m%d')
            else:
                # Fallback to timestamp if available
                timestamp = info.get('timestamp')
                if timestamp:
                    publish_date = datetime.fromtimestamp(timestamp)
                else:
                    raise ValueError("No upload date found")
            
            return VideoMetadata(
                video_id=video_id,
                title=info.get('title', 'Unknown Title'),
                publish_date=publish_date,
                channel_name=info.get('uploader', 'Unknown Channel'),
                description=info.get('description', ''),
                duration=str(info.get('duration', '')),
                view_count=info.get('view_count')
            )
            
    except ImportError:
        raise Exception("yt-dlp not installed. Install with: pip install yt-dlp")


def _get_metadata_web_scraping(video_id: str) -> VideoMetadata:
    """Fallback method using web scraping."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    html = response.text
    
    # Extract title
    title_match = re.search(r'"title":"([^"]+)"', html)
    title = title_match.group(1) if title_match else "Unknown Title"
    
    # Extract upload date (look for publishDate in JSON-LD)
    date_patterns = [
        r'"publishDate":"([^"]+)"',
        r'"datePublished":"([^"]+)"',
        r'itemprop="datePublished" content="([^"]+)"'
    ]
    
    publish_date = None
    for pattern in date_patterns:
        date_match = re.search(pattern, html)
        if date_match:
            date_str = date_match.group(1)
            try:
                # Try parsing ISO format
                publish_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                break
            except:
                continue
    
    if not publish_date:
        raise ValueError("Could not extract publish date from page")
    
    # Extract channel name
    channel_match = re.search(r'"author":"([^"]+)"', html)
    channel_name = channel_match.group(1) if channel_match else "Unknown Channel"
    
    # Extract description (first part)
    desc_match = re.search(r'"shortDescription":"([^"]+)"', html)
    description = desc_match.group(1) if desc_match else ""
    
    return VideoMetadata(
        video_id=video_id,
        title=title,
        publish_date=publish_date,
        channel_name=channel_name,
        description=description
    )


def format_video_context(metadata: VideoMetadata) -> str:
    """Format video metadata for use in agent prompts."""
    return f"""VIDEO CONTEXT:
- Video ID: {metadata.video_id}
- Title: {metadata.title}
- Published: {metadata.publish_date.strftime('%B %d, %Y')}
- Channel: {metadata.channel_name}
- Publication Date for Temporal Context: {metadata.publish_date.isoformat()}

This video was published on {metadata.publish_date.strftime('%B %d, %Y')}. Consider this temporal context when evaluating claims - statements should be assessed based on information available at the time of publication."""
