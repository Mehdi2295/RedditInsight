import requests
import time
import random
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.safari.service import Service as SafariService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import re
import urllib.parse
import json

class Scraper(ABC):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'
        }
        
    @abstractmethod
    def search(self, keyword, timeframe):
        pass
    
    def get_date_limit(self, timeframe):
        now = datetime.now()
        if timeframe == "week":
            return now - timedelta(days=7)
        elif timeframe == "month":
            return now - timedelta(days=30)
        elif timeframe == "year":
            return now - timedelta(days=365)
        else:  # Default to all time
            return datetime(2000, 1, 1)

class RedditScraper(Scraper):
    def __init__(self):
        super().__init__()
        
    def search(self, keyword, timeframe):
        print(f"Searching Reddit for '{keyword}' within timeframe: {timeframe}")
        date_limit = self.get_date_limit(timeframe)
        
        # Use Reddit's JSON API directly (more reliable than scraping)
        try:
            # Create URL for Reddit search
            search_query = urllib.parse.quote(f"{keyword}")
            
            # Map timeframe to Reddit's time filters
            time_filter = "all"
            if timeframe == "week":
                time_filter = "week"
            elif timeframe == "month":
                time_filter = "month"
            elif timeframe == "year":
                time_filter = "year"
            
            # Reddit search URL with JSON extension - increased limit to 100 (maximum allowed)
            search_url = f"https://www.reddit.com/search.json?q={search_query}&sort=relevance&t={time_filter}&limit=100"
            
            response = requests.get(
                search_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'
                }
            )
            
            if response.status_code != 200:
                print(f"Error: Reddit API request failed with status code {response.status_code}")
                return []
            
            # Parse JSON response
            data = response.json()
            
            # Extract posts from response
            posts = []
            if 'data' in data and 'children' in data['data']:
                posts = data['data']['children']
            
            if not posts:
                print("No Reddit posts found")
                return []
            
            print(f"Found {len(posts)} potential Reddit posts")
            
            # Check if there's another page of results
            after = data['data'].get('after')
            
            # Get second page if available
            if after:
                second_page_url = f"https://www.reddit.com/search.json?q={search_query}&sort=relevance&t={time_filter}&limit=100&after={after}"
                try:
                    response = requests.get(
                        second_page_url,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'
                        }
                    )
                    
                    if response.status_code == 200:
                        second_page_data = response.json()
                        if 'data' in second_page_data and 'children' in second_page_data['data']:
                            posts.extend(second_page_data['data']['children'])
                            print(f"Added {len(second_page_data['data']['children'])} more posts from second page")
                except Exception as e:
                    print(f"Error fetching second page: {e}")
            
            # Process each post - increased from 10 to 25 posts
            results = []
            for post in posts[:25]:  # Limit to 25 posts
                try:
                    post_data = post['data']
                    
                    # Extract basic information
                    title = post_data.get('title', 'Untitled Post')
                    url = f"https://www.reddit.com{post_data.get('permalink')}"
                    subreddit = post_data.get('subreddit_name_prefixed', 'Unknown')
                    created_utc = post_data.get('created_utc', 0)
                    
                    # Convert UTC timestamp to datetime
                    post_date = datetime.fromtimestamp(created_utc)
                    
                    # Skip if the post is too old
                    if post_date < date_limit:
                        continue
                    
                    # Get post content
                    selftext = post_data.get('selftext', '')
                    
                    # If post has a link instead of text, add it
                    post_content = selftext
                    if not selftext and 'url' in post_data:
                        post_content = f"Link: {post_data['url']}"
                    
                    # Get comments separately
                    comments = []
                    try:
                        permalink = post_data.get('permalink')
                        if permalink:
                            comments = self._get_post_comments(permalink)
                    except Exception as e:
                        print(f"Error getting comments: {e}")
                    
                    # Create result with all data including comments
                    result = {
                        "title": title,
                        "url": url,
                        "source": "Reddit",
                        "community": subreddit,
                        "date": post_date.isoformat(),
                        "content": post_content,
                        "comments": comments  # Store comments separately
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    print(f"Error processing Reddit post: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Error searching Reddit: {e}")
            return []
    
    def _get_post_content_api(self, post_data):
        """Extract content from Reddit API post data"""
        content_parts = []
        
        # Add post text (if available)
        selftext = post_data.get('selftext', '')
        if selftext:
            content_parts.append(selftext)
        
        # If post has a link instead of text, add it
        if not selftext and 'url' in post_data:
            content_parts.append(f"Link: {post_data['url']}")
        
        # Format the content
        full_content = "\n\n".join(content_parts)
        
        return full_content
    
    def _get_post_comments(self, permalink):
        """Get ALL comments for a post using Reddit's JSON API"""
        try:
            # Request JSON data for the post and comments
            comments_url = f"https://www.reddit.com{permalink}.json?limit=500"  # Increased limit to get more comments
            
            response = requests.get(
                comments_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'
                }
            )
            
            if response.status_code != 200:
                return []
            
            # Parse JSON
            data = response.json()
            
            # Comments are in the second element of the array
            if len(data) < 2 or 'data' not in data[1] or 'children' not in data[1]['data']:
                return []
            
            comments_data = data[1]['data']['children']
            
            # Extract ALL comments - removed the 15 comment limit
            comments = []
            for comment_obj in comments_data:
                if 'data' in comment_obj and 'body' in comment_obj['data']:
                    comment_body = comment_obj['data']['body']
                    author = comment_obj['data'].get('author', 'Anonymous')
                    score = comment_obj['data'].get('score', 0)
                    
                    if comment_body and comment_body != "[deleted]" and comment_body != "[removed]":
                        # Create structured comment object
                        comment = {
                            "author": f"u/{author}",
                            "score": score,
                            "body": comment_body,
                            "replies": []
                        }
                        
                        # Also get ALL replies to this comment - removed the 3 reply limit
                        if 'replies' in comment_obj['data'] and comment_obj['data']['replies']:
                            try:
                                # Process all reply levels
                                self._process_comment_replies(comment_obj['data']['replies'], comment["replies"])
                            except Exception as e:
                                print(f"Error fetching replies: {e}")
                        
                        comments.append(comment)
            
            print(f"Retrieved {len(comments)} comments for post")
            return comments
            
        except Exception as e:
            print(f"Error fetching comments: {e}")
            return []
    
    def _process_comment_replies(self, replies_obj, target_list):
        """Process nested comment replies recursively"""
        if not replies_obj or not isinstance(replies_obj, dict):
            return
            
        if 'data' not in replies_obj or 'children' not in replies_obj['data']:
            return
            
        replies_data = replies_obj['data']['children']
        
        for reply_obj in replies_data:
            if 'data' in reply_obj and 'body' in reply_obj['data']:
                reply_body = reply_obj['data']['body']
                reply_author = reply_obj['data'].get('author', 'Anonymous')
                reply_score = reply_obj['data'].get('score', 0)
                
                if reply_body and reply_body != "[deleted]" and reply_body != "[removed]":
                    reply = {
                        "author": f"u/{reply_author}",
                        "score": reply_score,
                        "body": reply_body,
                        "replies": []
                    }
                    
                    # Process nested replies recursively
                    if 'replies' in reply_obj['data'] and reply_obj['data']['replies']:
                        self._process_comment_replies(reply_obj['data']['replies'], reply["replies"])
                        
                    target_list.append(reply)
    
    def _extract_subreddit(self, url):
        """Extract subreddit name from URL"""
        try:
            # Pattern: https://www.reddit.com/r/SUBREDDIT/...
            match = re.search(r'reddit\.com/r/([^/]+)', url)
            if match:
                return 'r/' + match.group(1)
            return "Unknown Subreddit"
        except:
            return "Unknown Subreddit"
    
    def _parse_relative_date(self, date_text):
        now = datetime.now()
        
        if not date_text:
            return now
            
        # Fix for the split error - ensure date_text is a string
        if date_text is None:
            return now
            
        if "minute" in date_text:
            # Find the number of minutes safely
            match = re.search(r'\d+', date_text)
            minutes = int(match.group()) if match else 0
            return now - timedelta(minutes=minutes)
        elif "hour" in date_text:
            match = re.search(r'\d+', date_text)
            hours = int(match.group()) if match else 0
            return now - timedelta(hours=hours)
        elif "day" in date_text:
            match = re.search(r'\d+', date_text)
            days = int(match.group()) if match else 0
            return now - timedelta(days=days)
        elif "month" in date_text:
            match = re.search(r'\d+', date_text)
            months = int(match.group()) if match else 0
            return now - timedelta(days=months*30)
        elif "year" in date_text:
            match = re.search(r'\d+', date_text)
            years = int(match.group()) if match else 0
            return now - timedelta(days=years*365)
        else:
            return now
    
    def _get_post_content(self, url):
        """Fallback method to get content using Safari if API fails"""
        try:
            # Use Safari WebDriver
            driver = webdriver.Safari()
            
            driver.get(url)
            
            # Wait for content to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.Post, div[data-test-id='post-content']"))
                )
                
                # Get post content (try different selectors)
                post_content = ""
                selectors = [
                    "div[data-test-id='post-content']", 
                    "div.Post div[data-click-id='text']",
                    "div.Post div.md"
                ]
                
                for selector in selectors:
                    post_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if post_elements:
                        post_content = post_elements[0].text
                        break
                
                if not post_content:
                    post_content = "Content could not be extracted"
                
                # Get ALL comments - removed the limit
                comments = []
                comment_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='comment'], div.Comment")
                
                print(f"Found {len(comment_elements)} comments via Safari WebDriver")
                
                for comment_element in comment_elements:
                    try:
                        author_element = comment_element.find_element(By.CSS_SELECTOR, "a[data-testid='comment_author']")
                        author = author_element.text if author_element else "Anonymous"
                        
                        # Try to find score
                        score_element = comment_element.find_element(By.CSS_SELECTOR, "div[data-testid='comment-score']")
                        score_text = score_element.text if score_element else "0 points"
                        score = int(re.search(r'\d+', score_text).group()) if re.search(r'\d+', score_text) else 0
                        
                        # Find comment text
                        body_element = comment_element.find_element(By.CSS_SELECTOR, "div[data-testid='comment-content']")
                        body = body_element.text if body_element else ""
                        
                        if body:
                            comments.append({
                                "author": author,
                                "score": score,
                                "body": body,
                                "replies": []
                            })
                    except Exception as e:
                        print(f"Error processing comment: {e}")
                        continue
                
                return {
                    "content": post_content,
                    "comments": comments
                }
            except Exception as e:
                print(f"Error finding Reddit content elements: {e}")
                return {"content": "Content could not be retrieved", "comments": []}
            
        except Exception as e:
            print(f"Error fetching Reddit post content: {e}")
            return {"content": "Content could not be retrieved", "comments": []}
        finally:
            driver.quit() 