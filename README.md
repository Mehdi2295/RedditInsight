# RedditInsight

<div align="center">
  <img src="https://raw.githubusercontent.com/github/explore/80688e429a7d4ef2fca1e82350fe8e3517d3494d/topics/reddit/reddit.png" alt="Reddit Logo" width="100">
  <h3>Advanced Reddit analytics and data collection tool</h3>
</div>

## Overview

RedditInsight is a powerful analytics tool that scrapes, collects, and analyzes content from Reddit. Whether you're conducting market research, analyzing trends, or gathering insights on specific topics, RedditInsight provides the data and analysis tools you need.

## Key Features

- 🔍 **Smart Content Collection**: Search and collect Reddit posts, comments, and metadata with customizable search parameters
- ⏱️ **Flexible Time Filtering**: Analyze content from the past week, month, year, or all time
- 📊 **Sentiment Analysis**: Automatically analyze and categorize content sentiment using NLTK's VADER
- 📈 **Content Analysis**: Extract common words, phrases, and generate concise summaries
- 🔄 **Data Export**: Save your findings in JSON or CSV format for further analysis
- 💾 **Persistent Storage**: Access historical searches via integrated SQLite database
- 🖥️ **Dual Interfaces**: Choose between full-featured GUI or lightweight CLI

## Screenshots

*(Coming soon)*

## Installation

### Prerequisites

- Python 3.8 or higher
- Safari browser (for web scraping)

### Setup Instructions

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/RedditInsight.git
   cd RedditInsight
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Safari WebDriver:
   - Enable the Develop menu: Safari → Preferences → Advanced → "Show Develop menu in menu bar"
   - Enable Remote Automation: Develop → Allow Remote Automation
   - Authorize WebDriver: Run `safaridriver --enable` in Terminal

## Usage

### GUI Mode

Launch the graphical user interface for the most user-friendly experience:

```bash
python run.py
```

The GUI provides an intuitive interface for searching, viewing results, and generating analyses.

### CLI Mode

For headless environments or simplified usage, use the command-line interface:

```bash
python run_cli.py
```

Or with specific parameters:

```bash
python app.py -k "keyword" -t month -o json -l 20
```

Parameters:
- `-k, --keyword`: Search keyword (required)
- `-t, --timeframe`: Timeframe for search (`week`, `month`, `year`, `all`) [default: `month`]
- `-o, --output`: Output format (`json`, `csv`) [default: `json`]
- `-f, --filename`: Custom output filename (without extension)
- `-l, --limit`: Maximum number of results [default: 25]

## Technical Architecture

RedditInsight is built with a modular architecture that separates data collection, processing, storage, and visualization:

- **scraper.py**: Handles data collection from Reddit using their JSON API
- **processor.py**: Performs sentiment analysis, word frequency analysis, and content summarization
- **database.py**: Manages data persistence with SQLite
- **main.py**: Implements the PyQt6-based GUI
- **app.py/run_cli.py**: Provides command-line interfaces

### Data Flow

1. User initiates a search with keyword and parameters
2. RedditScraper collects matching posts from Reddit
3. Processor analyzes content for sentiment, common terms, and patterns
4. Results are stored in the SQLite database and displayed to the user
5. Analysis can be exported in preferred format

## Advanced Usage

### Custom Analysis

The Processor class can be extended to implement custom analysis algorithms:

```python
from processor import Processor

class CustomProcessor(Processor):
    def __init__(self):
        super().__init__()
        
    def my_custom_analysis(self, results):
        # Implement custom analysis logic
        pass
```

## Limitations

- **Rate Limiting**: Excessive requests may be rate-limited by Reddit
- **Content Accessibility**: Private or restricted content cannot be scraped
- **Analysis Precision**: Sentiment analysis provides approximations based on lexical analysis

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- [NLTK](https://www.nltk.org/) for natural language processing capabilities
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the graphical interface
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing 