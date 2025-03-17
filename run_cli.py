#!/usr/bin/env python3
"""
Reddit Scraper - CLI Version
This script provides a command-line interface for the scraper.
Use this if you encounter issues with PyQt.
"""

import sys
import subprocess
import importlib
import os
import time
import json
from pathlib import Path

def check_dependencies(gui_required=False):
    """Check if required packages are installed"""
    # Core dependencies that don't include PyQt
    core_packages = [
        "beautifulsoup4",
        "requests",
        "selenium",
        "python-dateutil",
        "lxml",
        "webdriver-manager",
        "nltk"
    ]
    
    # Only check PyQt if GUI is required
    if gui_required:
        core_packages.append("PyQt6")
    
    missing_packages = []
    
    for package in core_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("The following dependencies are missing:")
        for package in missing_packages:
            print(f"  - {package}")
        
        install = input("Would you like to install them now? (y/n): ")
        if install.lower() == 'y':
            try:
                for package in missing_packages:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print("Dependencies installed successfully.")
                return True
            except subprocess.CalledProcessError:
                print("Error installing dependencies. Please install them manually.")
                return False
        else:
            print("Dependencies required to run the application.")
            return False
    
    return True

def run_cli_scraper():
    """Run the scraper in CLI mode"""
    # Import only after dependencies are confirmed
    from scraper import RedditScraper
    from database import Database
    from processor import Processor
    
    db = Database()
    processor = Processor()
    
    print("========================================")
    print("Reddit Content Scraper - CLI Mode")
    print("========================================")
    print()
    
    keyword = input("Enter a keyword to search for: ")
    if not keyword:
        print("Error: Keyword cannot be empty.")
        return
    
    print("\nSelect timeframe:")
    print("1. All Time")
    print("2. Last Week")
    print("3. Last Month")
    print("4. Last Year")
    
    timeframe_choice = input("Enter your choice (1-4): ")
    timeframe_mapping = {
        "1": "all",
        "2": "week",
        "3": "month",
        "4": "year"
    }
    
    if timeframe_choice not in timeframe_mapping:
        print("Invalid choice. Using All Time as default.")
        timeframe = "all"
    else:
        timeframe = timeframe_mapping[timeframe_choice]
    
    print("\nStarting search...")
    results = []
    
    # Search Reddit
    print(f"Searching Reddit for '{keyword}'...")
    reddit_scraper = RedditScraper()
    reddit_results = reddit_scraper.search(keyword, timeframe)
    results.extend(reddit_results)
    print(f"Found {len(reddit_results)} results from Reddit")
    
    # Save results
    if results:
        db.save_results(results, keyword)
        db.save_search(keyword, timeframe)
        print(f"\nTotal results found: {len(results)}")
        
        # Show a brief summary of results
        print("\nResults Summary:")
        for i, result in enumerate(results[:5], 1):  # Show first 5 results
            print(f"{i}. {result.get('title', 'Untitled')} ({result.get('source', 'Unknown')})")
        
        if len(results) > 5:
            print(f"... and {len(results) - 5} more.")
        
        # Offer to generate analysis
        analyze = input("\nGenerate analysis? (y/n): ").lower() == 'y'
        if analyze:
            print("\nGenerating analysis...")
            analysis = processor.analyze_results(results)
            report = processor.generate_text_report(analysis, keyword)
            print("\n" + report)
        
        # Offer to export results
        export = input("\nExport results? (y=yes, n=no): ").lower()
        if export == 'y':
            export_format = input("Export format (json/csv): ").lower()
            
            if export_format == 'json':
                output_path = db.export_results_to_json(keyword)
                print(f"Results exported to {output_path}")
            elif export_format == 'csv':
                output_path = db.export_results_to_csv(keyword)
                print(f"Results exported to {output_path}")
            else:
                print("Invalid format. Export cancelled.")
    else:
        print("No results found.")

def main():
    """Main entry point"""
    print("Starting Reddit Content Scraper (CLI Version)...")
    
    # Check dependencies (GUI not required)
    if not check_dependencies(gui_required=False):
        return
    
    # Download NLTK data
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
    except Exception as e:
        print(f"Warning: Could not download NLTK data: {str(e)}")
        print("Some analysis features may not work correctly.")
    
    # Run CLI scraper
    run_cli_scraper()

if __name__ == "__main__":
    main() 