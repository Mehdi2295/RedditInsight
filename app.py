import sys
import argparse
from scraper import RedditScraper
from processor import Processor
from database import Database
import json

def get_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Web scraping tool for Reddit')
    parser.add_argument('--keyword', '-k', type=str, help='Search keyword')
    parser.add_argument('--timeframe', '-t', type=str, choices=['week', 'month', 'year', 'all'], 
                        default='month', help='Timeframe for search (default: month)')
    parser.add_argument('--output', '-o', type=str, default='json', 
                        choices=['json', 'csv'], help='Output format (default: json)')
    parser.add_argument('--filename', '-f', type=str, help='Output filename (without extension)')
    parser.add_argument('--limit', '-l', type=int, default=25, help='Maximum number of results to return (default: 25)')
    
    return parser.parse_args()

def run_cli():
    """Run the application in CLI mode"""
    
    # Parse command line arguments
    args = get_args()
    
    # If keyword not provided, prompt user
    keyword = args.keyword
    if not keyword:
        keyword = input("Enter search keyword: ")
    
    # If timeframe not provided, prompt user
    timeframe = args.timeframe
    if not timeframe:
        timeframe_options = ['week', 'month', 'year', 'all']
        print("Select timeframe:")
        for i, option in enumerate(timeframe_options, 1):
            print(f"{i}. {option.capitalize()}")
        
        choice = 0
        while choice < 1 or choice > len(timeframe_options):
            try:
                choice = int(input("Enter your choice (1-4): "))
            except ValueError:
                choice = 0
        
        timeframe = timeframe_options[choice-1]
    
    # Initialize components
    reddit_scraper = RedditScraper()
    processor = Processor()
    db = Database()
    
    # Perform search
    print(f"Searching for '{keyword}' within timeframe: {timeframe}")
    
    # Search Reddit
    results = reddit_scraper.search(keyword, timeframe)
    print(f"Found {len(results)} results from Reddit")
    
    # Apply limit if specified
    if args.limit and args.limit < len(results):
        results = results[:args.limit]
        print(f"Limited to {len(results)} results as requested")
    
    # Process the results
    processed_data = processor.process_results(results, keyword)
    
    # Save to database
    db.save_results(processed_data["processed_data"], keyword)
    
    # Also save the search query to history
    db.save_search(keyword, timeframe)
    
    # Display analysis
    print("\n" + "="*50)
    print("ANALYSIS REPORT")
    print("="*50)
    print(processed_data["analysis"]["summary"])
    print("="*50)
    
    # Export results
    output_file = processor.export_results(
        processed_data["processed_data"], 
        output_format=args.output, 
        filename=args.filename
    )
    
    print(f"\nResults exported to: {output_file}")
    
    # Display comment details
    print("\nWould you like to see detailed comments for a specific post? (y/n)")
    choice = input().lower()
    
    if choice == 'y':
        print("\nAvailable posts:")
        for i, post in enumerate(processed_data["processed_data"], 1):
            print(f"{i}. {post['title']} ({post['source']})")
        
        post_choice = 0
        max_choice = len(processed_data["processed_data"])
        
        while post_choice < 1 or post_choice > max_choice:
            try:
                post_choice = int(input(f"Enter post number (1-{max_choice}): "))
            except ValueError:
                post_choice = 0
        
        # Display selected post details
        selected_post = processed_data["processed_data"][post_choice-1]
        print("\n" + "="*50)
        print(f"TITLE: {selected_post['title']}")
        print(f"SOURCE: {selected_post['source']} - {selected_post['community']}")
        print(f"URL: {selected_post['url']}")
        print(f"DATE: {selected_post['date']}")
        print("="*50)
        print("CONTENT:")
        print(selected_post['content'])
        
        # Display comments if available
        if 'comments' in selected_post and selected_post['comments']:
            print("\nCOMMENTS:")
            
            for i, comment in enumerate(selected_post['comments'], 1):
                # Handle the new structured comment format
                if isinstance(comment, dict) and 'author' in comment and 'body' in comment:
                    author = comment.get('author', 'Anonymous')
                    score = comment.get('score', 0)
                    body = comment.get('body', '')
                    
                    print(f"\n{i}. {author} ({score} points):")
                    print(f"   {body}")
                    
                    # Show replies if any
                    if 'replies' in comment and comment['replies']:
                        for j, reply in enumerate(comment['replies'], 1):
                            if isinstance(reply, dict):
                                reply_author = reply.get('author', 'Anonymous')
                                reply_score = reply.get('score', 0)
                                reply_body = reply.get('body', '')
                                
                                print(f"\n   {i}.{j} ↳ {reply_author} ({reply_score} points):")
                                print(f"      {reply_body}")
                else:
                    # Fallback for old format or string comments
                    print(f"\n{i}. {comment}")
        else:
            print("\nNo comments available for this post.")
    
    return processed_data

if __name__ == "__main__":
    run_cli() 