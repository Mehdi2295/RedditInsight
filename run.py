#!/usr/bin/env python3
"""
Reddit Scraper Launcher
This script checks for necessary dependencies and launches the application.
"""

import sys
import subprocess
import importlib
import pkg_resources
import os
from pathlib import Path

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = []
    
    try:
        with open('requirements.txt', 'r') as f:
            required_packages = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("Error: requirements.txt not found.")
        return False
    
    missing_packages = []
    
    for package in required_packages:
        package_name = package.split('==')[0]
        try:
            importlib.import_module(package_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("The following dependencies are missing:")
        for package in missing_packages:
            print(f"  - {package}")
        
        install = input("Would you like to install them now? (y/n): ")
        if install.lower() == 'y':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                print("Dependencies installed successfully.")
                return True
            except subprocess.CalledProcessError:
                print("Error installing dependencies. Please install them manually using:")
                print(f"pip install -r requirements.txt")
                return False
        else:
            print("Dependencies required to run the application.")
            return False
    
    return True

def main():
    """Main entry point"""
    print("Starting Reddit Content Scraper...")
    
    # Check if running from the correct directory
    if not os.path.exists('main.py'):
        print("Error: Please run this script from the project root directory.")
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Download NLTK data
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
    except Exception as e:
        print(f"Warning: Could not download NLTK data: {str(e)}")
        print("Some analysis features may not work correctly.")
    
    # Start the application
    print("Launching application...")
    try:
        import main
        main.app = main.QApplication(sys.argv)
        main.window = main.ScraperApp()
        main.window.show()
        sys.exit(main.app.exec())
    except Exception as e:
        print(f"Error starting application: {str(e)}")

if __name__ == "__main__":
    main() 