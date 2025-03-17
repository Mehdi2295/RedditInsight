import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from collections import Counter
import string
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
import json
from datetime import datetime
import os

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class Processor:
    def __init__(self):
        # Initialize stopwords - with error handling
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            print("Warning: Could not load stopwords, using a minimal set instead")
            self.stop_words = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 
                                'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 
                                'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 
                                'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 
                                'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 
                                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 
                                'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 
                                'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 
                                'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 
                                'through', 'during', 'before', 'after', 'above', 'below', 'to', 
                                'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 
                                'again', 'further', 'then', 'once', 'here', 'there', 'when', 
                                'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
                                'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 
                                'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 
                                'don', 'should', 'now'])
        
        # Download required NLTK resources
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')
        
        self.sia = SentimentIntensityAnalyzer()
    
    def analyze_results(self, results):
        """
        Analyze a list of results to extract key insights
        Returns a dictionary with analysis data
        """
        if not results:
            return {
                "total_results": 0,
                "sources": {},
                "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
                "common_words": [],
                "common_phrases": [],
                "summary": "No results to analyze."
            }
        
        try:
            # Extract basic stats
            analysis = {
                "total_results": len(results),
                "sources": self._count_sources(results),
                "sentiment": self._analyze_sentiment(results),
                "common_words": self._extract_common_words(results),
                "common_phrases": self._extract_common_phrases(results),
                "summary": self._generate_summary(results)
            }
            
            return analysis
        except Exception as e:
            print(f"Error during analysis: {e}")
            # Return basic data even if analysis fails
            return {
                "total_results": len(results),
                "sources": self._count_sources(results),
                "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
                "common_words": [],
                "common_phrases": [],
                "summary": f"Analysis could not be completed: {str(e)}"
            }
    
    def _count_sources(self, results):
        """Count results by source (Reddit)"""
        sources = {}
        for result in results:
            source = result.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        return sources
    
    def _analyze_sentiment(self, results):
        """
        Simple sentiment analysis based on positive/negative word counts
        More sophisticated sentiment analysis could be implemented with external libraries
        """
        positive_words = set([
            'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic',
            'wonderful', 'best', 'love', 'recommend', 'positive', 'perfect',
            'helpful', 'impressive', 'better', 'easy', 'top', 'favorite',
            'satisfied', 'worth', 'nice', 'happy', 'reliable', 'effective'
        ])
        
        negative_words = set([
            'bad', 'poor', 'terrible', 'awful', 'horrible', 'worst',
            'hate', 'negative', 'difficult', 'broken', 'annoying', 'avoid',
            'disappointing', 'issue', 'problem', 'bug', 'error', 'crash',
            'slow', 'expensive', 'overpriced', 'useless', 'confusing', 'fail'
        ])
        
        sentiment = {"positive": 0, "neutral": 0, "negative": 0}
        
        for result in results:
            try:
                content = result.get('content', '') or ''  # Ensure content is never None
                title = result.get('title', '') or ''      # Ensure title is never None
                
                text = title + " " + content
                
                pos_count = sum(1 for word in text.split() if word in positive_words)
                neg_count = sum(1 for word in text.split() if word in negative_words)
                
                if pos_count > neg_count:
                    sentiment["positive"] += 1
                elif neg_count > pos_count:
                    sentiment["negative"] += 1
                else:
                    sentiment["neutral"] += 1
            except Exception as e:
                print(f"Error analyzing sentiment for a result: {e}")
                sentiment["neutral"] += 1  # Default to neutral on error
                
        return sentiment
    
    def _extract_common_words(self, results, top_n=20):
        """Extract most common words from all results content"""
        try:
            all_text = " ".join([(result.get('title', '') or '') + " " + (result.get('content', '') or '') for result in results])
            
            # Tokenize and clean
            try:
                tokens = word_tokenize(all_text.lower())
            except:
                # Fall back to simple splitting if NLTK tokenizer fails
                tokens = all_text.lower().split()
                
            tokens = [word for word in tokens 
                    if word not in self.stop_words
                    and word not in string.punctuation
                    and len(word) > 2]
            
            # Get frequency distribution
            fdist = FreqDist(tokens)
            return fdist.most_common(top_n)
        except Exception as e:
            print(f"Error extracting common words: {e}")
            return []
    
    def _extract_common_phrases(self, results, top_n=10):
        """Extract common 2-3 word phrases (bigrams and trigrams)"""
        try:
            all_text = " ".join([(result.get('title', '') or '') + " " + (result.get('content', '') or '') for result in results])
            
            # Tokenize sentences and words
            try:
                sentences = sent_tokenize(all_text)
            except:
                # Fall back to simple period splitting if NLTK tokenizer fails
                sentences = all_text.split('.')
            
            # Extract bigrams and trigrams
            bigrams = []
            trigrams = []
            
            for sentence in sentences:
                try:
                    words = [word.lower() for word in word_tokenize(sentence) 
                            if word.lower() not in self.stop_words
                            and word not in string.punctuation
                            and len(word) > 2]
                except:
                    # Fall back to simple word splitting
                    words = [word.lower() for word in sentence.split() 
                            if word.lower() not in self.stop_words
                            and word not in string.punctuation
                            and len(word) > 2]
                
                # Add bigrams
                for i in range(len(words) - 1):
                    bigrams.append(f"{words[i]} {words[i+1]}")
                
                # Add trigrams
                for i in range(len(words) - 2):
                    trigrams.append(f"{words[i]} {words[i+1]} {words[i+2]}")
            
            # Count frequencies
            bigram_counter = Counter(bigrams)
            trigram_counter = Counter(trigrams)
            
            # Combine and get top phrases
            phrases = []
            for phrase, count in bigram_counter.most_common(top_n//2):
                phrases.append((phrase, count))
                
            for phrase, count in trigram_counter.most_common(top_n//2):
                phrases.append((phrase, count))
                
            return sorted(phrases, key=lambda x: x[1], reverse=True)[:top_n]
        except Exception as e:
            print(f"Error extracting common phrases: {e}")
            return []
    
    def _generate_summary(self, results, max_sentences=10):
        """Generate a brief summary of the results"""
        try:
            # Extract all sentences
            all_sentences = []
            for result in results:
                content = result.get('content', '') or ''  # Ensure content is never None
                try:
                    sentences = sent_tokenize(content)
                except:
                    # Fall back to simple period splitting if NLTK tokenizer fails
                    sentences = content.split('.')
                all_sentences.extend(sentences)
            
            # If there are very few sentences, return them directly
            if len(all_sentences) <= max_sentences:
                return " ".join(all_sentences)
            
            # Score each sentence based on word frequency
            all_text = " ".join(all_sentences)
            try:
                words = word_tokenize(all_text.lower())
            except:
                # Fall back to simple word splitting
                words = all_text.lower().split()
                
            words = [word for word in words 
                    if word not in self.stop_words
                    and word not in string.punctuation]
            
            word_frequencies = Counter(words)
            
            # Calculate sentence scores
            sentence_scores = {}
            for sentence in all_sentences:
                if not sentence.strip():  # Skip empty sentences
                    continue
                    
                try:
                    sentence_words = word_tokenize(sentence.lower())
                except:
                    sentence_words = sentence.lower().split()
                    
                for word in sentence_words:
                    if word in word_frequencies:
                        if sentence in sentence_scores:
                            sentence_scores[sentence] += word_frequencies[word]
                        else:
                            sentence_scores[sentence] = word_frequencies[word]
            
            # Get top sentences
            summary_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:max_sentences]
            summary = " ".join([sentence for sentence, score in summary_sentences])
            
            return summary
        except Exception as e:
            print(f"Error generating summary: {e}")
            if results and len(results) > 0:
                # Return first result title as fallback
                return f"Could not generate summary. Sample title: {results[0].get('title', '')}"
            return "Could not generate summary."
    
    def generate_text_report(self, analysis, search_term):
        """Generate a formatted text report from analysis data"""
        try:
            report = f"=== Analysis Report for '{search_term}' ===\n\n"
            
            # Basic stats
            report += f"Total results: {analysis.get('total_results', 0)}\n"
            
            sources = analysis.get('sources', {})
            if sources:
                report += f"Sources: {', '.join([f'{src} ({count})' for src, count in sources.items()])}\n\n"
            
            # Sentiment
            sentiment = analysis.get('sentiment', {"positive": 0, "neutral": 0, "negative": 0})
            report += "Sentiment Analysis:\n"
            total = sum(sentiment.values())
            if total > 0:
                report += f"  Positive: {sentiment['positive']} ({sentiment['positive']/total*100:.1f}%)\n"
                report += f"  Neutral: {sentiment['neutral']} ({sentiment['neutral']/total*100:.1f}%)\n"
                report += f"  Negative: {sentiment['negative']} ({sentiment['negative']/total*100:.1f}%)\n\n"
            
            # Common words
            common_words = analysis.get('common_words', [])
            if common_words:
                report += "Common Words:\n"
                for word, count in common_words[:10]:
                    report += f"  {word}: {count}\n"
                report += "\n"
            
            # Common phrases
            common_phrases = analysis.get('common_phrases', [])
            if common_phrases:
                report += "Common Phrases:\n"
                for phrase, count in common_phrases[:5]:
                    report += f"  {phrase}: {count}\n"
                report += "\n"
            
            # Summary
            summary = analysis.get('summary', '')
            if summary:
                report += "Summary:\n"
                report += summary
            
            return report
        except Exception as e:
            print(f"Error generating report: {e}")
            return f"Error generating report: {str(e)}"
    
    def format_results_for_display(self, results):
        """Format results for display in the UI"""
        formatted = []
        
        for result in results:
            try:
                title = result.get('title', 'Untitled')
                source = result.get('source', 'Unknown')
                community = result.get('community', '')
                date = result.get('date', '')
                url = result.get('url', '')
                
                # Truncate content for display
                content = result.get('content', '')
                if content and len(content) > 300:
                    content = content[:297] + '...'
                
                formatted.append({
                    'title': title,
                    'source': source,
                    'community': community,
                    'date': date,
                    'url': url,
                    'content': content,
                    'full_result': result  # Keep reference to full result
                })
            except Exception as e:
                print(f"Error formatting result for display: {e}")
                # Add a placeholder for the error result
                formatted.append({
                    'title': 'Error formatting result',
                    'source': 'Unknown',
                    'community': '',
                    'date': '',
                    'url': '',
                    'content': f'Error: {str(e)}',
                    'full_result': result
                })
            
        return formatted 

    def process_results(self, results, search_term):
        """Process the scraped results to extract insights"""
        if not results:
            return {
                "total_results": 0,
                "message": "No results found for the given search term and timeframe."
            }
        
        # Create a DataFrame from the results
        df = pd.DataFrame(results)
        
        # Add a unique ID to each result
        df['id'] = range(1, len(df) + 1)
        
        # Add the search term and current timestamp
        df['search_term'] = search_term
        df['created_at'] = datetime.now().isoformat()
        
        # Run analysis
        sentiment_data = self._analyze_sentiment(df)
        word_freq = self._analyze_word_frequency(df)
        summary = self._generate_summary(df, sentiment_data, word_freq)
        
        # Return both the processed data and the analysis summary
        return {
            "processed_data": df.to_dict('records'),
            "analysis": {
                "sentiment": sentiment_data,
                "word_frequency": word_freq,
                "summary": summary
            }
        }
    
    def _analyze_sentiment(self, df):
        """Analyze sentiment of the content"""
        sentiments = []
        
        for _, row in df.iterrows():
            content_text = row['content']
            
            # Also analyze comments
            if 'comments' in row and row['comments']:
                # Process structured comments
                all_comment_text = ""
                for comment in row['comments']:
                    if isinstance(comment, dict) and 'body' in comment:
                        all_comment_text += " " + comment['body']
                        
                        # Include replies
                        if 'replies' in comment and comment['replies']:
                            for reply in comment['replies']:
                                if isinstance(reply, dict) and 'body' in reply:
                                    all_comment_text += " " + reply['body']
                
                # Combine post content with comments for complete sentiment
                content_text = content_text + " " + all_comment_text
            
            # Get sentiment scores
            sentiment = self.sia.polarity_scores(content_text)
            
            # Categorize the sentiment
            if sentiment['compound'] >= 0.05:
                category = 'positive'
            elif sentiment['compound'] <= -0.05:
                category = 'negative'
            else:
                category = 'neutral'
            
            sentiments.append({
                'id': row['id'],
                'title': row['title'],
                'compound': sentiment['compound'],
                'positive': sentiment['pos'],
                'negative': sentiment['neg'],
                'neutral': sentiment['neu'],
                'category': category
            })
        
        # Create a summary of sentiments
        sentiment_df = pd.DataFrame(sentiments)
        sentiment_summary = {
            'total': len(sentiment_df),
            'positive': len(sentiment_df[sentiment_df['category'] == 'positive']),
            'negative': len(sentiment_df[sentiment_df['category'] == 'negative']),
            'neutral': len(sentiment_df[sentiment_df['category'] == 'neutral']),
            'average_compound': sentiment_df['compound'].mean()
        }
        
        return {
            'details': sentiments,
            'summary': sentiment_summary
        }
    
    def _analyze_word_frequency(self, df):
        """Analyze word frequency in content"""
        # Combine all content and comments
        all_text = ""
        
        for _, row in df.iterrows():
            all_text += " " + row['content']
            
            # Also include comments in the analysis
            if 'comments' in row and row['comments']:
                # Process structured comments
                for comment in row['comments']:
                    if isinstance(comment, dict) and 'body' in comment:
                        all_text += " " + comment['body']
                        
                        # Include replies
                        if 'replies' in comment and comment['replies']:
                            for reply in comment['replies']:
                                if isinstance(reply, dict) and 'body' in reply:
                                    all_text += " " + reply['body']
        
        # Clean the text
        cleaned_text = re.sub(r'[^\w\s]', '', all_text.lower())
        
        # Tokenize
        words = word_tokenize(cleaned_text)
        
        # Remove stop words
        words = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        # Count word frequency
        word_counts = Counter(words)
        
        # Get the most common words
        most_common = word_counts.most_common(20)
        
        # Extract phrases (bigrams)
        bigrams = list(nltk.bigrams(words))
        bigram_counts = Counter(bigrams)
        common_phrases = bigram_counts.most_common(10)
        
        # Format the phrases
        formatted_phrases = [' '.join(phrase) for phrase, count in common_phrases]
        
        return {
            'common_words': {word: count for word, count in most_common},
            'common_phrases': formatted_phrases
        }
    
    def _generate_summary(self, df, sentiment_data, word_freq):
        """Generate a text summary of the findings"""
        summary = []
        
        # Basic stats
        total_results = len(df)
        sources = df['source'].value_counts().to_dict()
        
        summary.append(f"Analysis of {total_results} results for the search term.")
        
        # Add source breakdown
        source_text = []
        for source, count in sources.items():
            source_text.append(f"{count} from {source}")
        
        summary.append("Sources: " + ", ".join(source_text) + ".")
        
        # Add sentiment breakdown
        sentiment_summary = sentiment_data['summary']
        sentiment_text = f"Sentiment analysis: {sentiment_summary['positive']} positive, {sentiment_summary['negative']} negative, and {sentiment_summary['neutral']} neutral results."
        summary.append(sentiment_text)
        
        # Add most common words and phrases
        common_words = list(word_freq['common_words'].keys())[:5]
        common_phrases = word_freq['common_phrases'][:5]
        
        summary.append(f"Most common words: {', '.join(common_words)}.")
        
        if common_phrases:
            summary.append(f"Common phrases: {', '.join(common_phrases)}.")
        
        return "\n".join(summary)
    
    def export_results(self, processed_data, output_format='json', filename=None):
        """Export processed results to a file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results_{timestamp}"
        
        # Convert dataframe to the specified format
        if output_format.lower() == 'json':
            output_file = f"{filename}.json"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            
            # Ensure comments are properly included and structured
            for post in processed_data:
                # Make sure comments field exists
                if 'comments' not in post:
                    post['comments'] = []
                    
                # If comments exist but aren't in the correct format, fix them
                elif not isinstance(post['comments'], list):
                    post['comments'] = []
                    
                # Ensure each comment has all required fields
                for i, comment in enumerate(post['comments']):
                    if not isinstance(comment, dict):
                        # Convert string comments to proper format
                        post['comments'][i] = {
                            "author": "Unknown",
                            "score": 0,
                            "body": str(comment),
                            "replies": []
                        }
                    elif 'replies' not in comment:
                        comment['replies'] = []
            
            # Export as JSON with proper formatting
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            print(f"Exported {len(processed_data)} posts with {sum(len(post.get('comments', [])) for post in processed_data)} comments to JSON")
            
            return output_file
        
        elif output_format.lower() == 'csv':
            output_file = f"{filename}.csv"
            
            # Convert to DataFrame
            df = pd.DataFrame(processed_data)
            
            # Handle nested comment structures for CSV export
            if 'comments' in df.columns:
                # Serialize nested comments to string
                df['comments'] = df['comments'].apply(lambda x: json.dumps(x) if x else "")
            
            # Export as CSV
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            return output_file
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}") 