# RedditInsight

A comprehensive analytics tool that gathers threads from Reddit, stores them in a database, and provides in-depth analysis on the collected data.

## Features

- **Reddit Data Collection**: Search and collect posts from Reddit, including titles, content, and comments
- **Timeframe Selection**: Filter results by time period (week, month, year, or all time)
- **Sentiment Analysis**: Analyze the sentiment of collected posts (positive, negative, neutral)
- **Content Analysis**: Extract common words, phrases, and generate summaries
- **Data Export**: Export results in JSON or CSV format
- **Database Storage**: Store results in a SQLite database for future reference
- **Command Line Interface**: Easy-to-use CLI for searching and viewing results

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Clone this repository or download the source code
2. Navigate to the project directory
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file includes:

```
requests
beautifulsoup4
selenium
nltk
pandas
python-dateutil
PyQt6 # For GUI version
```

### Safari WebDriver Setup

This application uses Safari for web scraping. To enable Safari for automation:

1. Enable the Develop menu in Safari: Safari → Preferences → Advanced → Check "Show Develop menu in menu bar"
2. Enable Remote Automation: Develop → Allow Remote Automation
3. Authorize WebDriver: Run `safaridriver --enable` in Terminal

## Usage

### Command Line Interface

Run the CLI version with:

```bash
python app.py [-k KEYWORD] [-t TIMEFRAME] [-o OUTPUT_FORMAT] [-f FILENAME] [-l LIMIT]
```

Parameters:
- `-k, --keyword`: Search keyword
- `-t, --timeframe`: Timeframe for search (week, month, year, all) [default: month]
- `-o, --output`: Output format (json, csv) [default: json]
- `-f, --filename`: Output filename without extension
- `-l, --limit`: Maximum number of results to return [default: 25]

Example:
```bash
python app.py -k "artificial intelligence" -t month -o json -l 20
```

If no parameters are provided, the application will prompt for input.

### GUI Application (Coming Soon)

A graphical user interface is under development for easier interaction with the application.

## Technical Details

### Architecture

The application follows a modular structure:

- **scraper.py**: Contains the `RedditScraper` class for collecting data
- **processor.py**: Analyzes and processes the collected data
- **database.py**: Manages the SQLite database for storing and retrieving results
- **app.py**: Command-line interface for the application
- **main.py**: Main application logic
- **run.py** and **run_cli.py**: Entry points for different execution modes

### Data Collection Methods

- **Reddit**: Uses Reddit's JSON API to search for posts and comments

### Analysis Components

- **Sentiment Analysis**: Uses NLTK's VADER for sentiment scoring
- **Word Frequency**: Extracts and counts common words and phrases
- **Summarization**: Generates concise summaries of the collected content

## Limitations

- **Rate Limiting**: Excessive requests may be rate-limited by Reddit
- **Content Accessibility**: Some content may not be accessible due to privacy settings or community restrictions
- **Data Accuracy**: Sentiment analysis and summarization are approximations and may not perfectly capture the true sentiment or meaning

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 