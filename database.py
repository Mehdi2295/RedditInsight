import sqlite3
import json
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path="scraper_data.db"):
        self.db_path = db_path
        self.create_tables()
        
    def create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create results table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                community TEXT,
                date TEXT,
                content TEXT,
                search_term TEXT NOT NULL,
                created_at TEXT NOT NULL,
                comments TEXT
            )
            ''')
            
            # Create searches table to keep track of search history
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_term TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            ''')
            
            # Check if comments column exists, add it if not
            try:
                cursor.execute("SELECT comments FROM results LIMIT 1")
            except sqlite3.OperationalError:
                # Column doesn't exist, add it
                cursor.execute("ALTER TABLE results ADD COLUMN comments TEXT")
            
            conn.commit()
    
    def save_results(self, results, search_term):
        """Save search results to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for result in results:
                # Convert comments to JSON string if they exist
                comments_json = None
                if 'comments' in result and result['comments']:
                    comments_json = json.dumps(result['comments'])
                
                cursor.execute('''
                INSERT INTO results 
                (title, url, source, community, date, content, search_term, created_at, comments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result.get('title', ''),
                    result.get('url', ''),
                    result.get('source', ''),
                    result.get('community', ''),
                    result.get('date', None),
                    result.get('content', ''),
                    search_term,
                    datetime.now().isoformat(),
                    comments_json
                ))
            
            conn.commit()
    
    def save_search(self, search_term, timeframe):
        """Save search query to history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO searches (search_term, timeframe, timestamp)
            VALUES (?, ?, ?)
            ''', (search_term, timeframe, datetime.now().isoformat()))
            conn.commit()
    
    def get_results(self, search_term=None, timeframe=None, source=None, limit=50):
        """Retrieve results with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM results"
            params = []
            
            # Build WHERE clause based on filters
            conditions = []
            
            if search_term:
                conditions.append("search_term = ?")
                params.append(search_term)
            
            if source:
                conditions.append("source = ?")
                params.append(source)
            
            if timeframe:
                # Convert timeframe to date limit
                now = datetime.now()
                date_limit = None
                
                if timeframe == "week":
                    date_limit = (now - timedelta(days=7)).isoformat()
                elif timeframe == "month":
                    date_limit = (now - timedelta(days=30)).isoformat()
                elif timeframe == "year":
                    date_limit = (now - timedelta(days=365)).isoformat()
                
                if date_limit:
                    conditions.append("date >= ?")
                    params.append(date_limit)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            # Parse comments from JSON
            for result in results:
                if 'comments' in result and result['comments']:
                    try:
                        result['comments'] = json.loads(result['comments'])
                    except:
                        result['comments'] = []
                else:
                    result['comments'] = []
            
            return results
    
    def get_search_history(self, limit=10):
        """Get recent search history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM searches 
            ORDER BY timestamp DESC 
            LIMIT ?
            ''', (limit,))
            
            history = [dict(row) for row in cursor.fetchall()]
            return history
    
    def export_results_to_json(self, search_term=None, output_path=None):
        """
        Export results to JSON file with organized folder structure:
        - Main 'results' folder
        - Subfolders for each date (YYYY-MM-DD)
        - Files named as {keyword}_{hour}.json
        """
        # Get all results including comments from the database
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM results"
            params = []
            
            if search_term:
                query += " WHERE search_term = ?"
                params.append(search_term)
            
            query += " ORDER BY date DESC LIMIT 1000"
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            # Parse comments from JSON string
            for result in results:
                if 'comments' in result and result['comments']:
                    try:
                        result['comments'] = json.loads(result['comments'])
                    except:
                        result['comments'] = []
                else:
                    result['comments'] = []
        
        # Create base results directory
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        # Get current date and time
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")
        
        # Create date folder
        date_dir = os.path.join(results_dir, date_str)
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)
        
        # Create filename with keyword and hour
        keyword = search_term if search_term else "all_results"
        filename = f"{keyword}_{hour_str}.json"
        output_path = os.path.join(date_dir, filename)
        
        # Write to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return output_path
        
    def export_results_to_csv(self, search_term=None, output_path=None):
        """
        Export results to CSV file with organized folder structure:
        - Main 'results' folder
        - Subfolders for each date (YYYY-MM-DD)
        - Files named as {keyword}_{hour}.csv
        """
        import csv
        
        # Get all results
        results = self.get_results(search_term=search_term, limit=1000)
        
        if not results:
            return None
        
        # Create base results directory
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        # Get current date and time
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        hour_str = now.strftime("%H")
        
        # Create date folder
        date_dir = os.path.join(results_dir, date_str)
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)
        
        # Create filename with keyword and hour
        keyword = search_term if search_term else "all_results"
        filename = f"{keyword}_{hour_str}.csv"
        output_path = os.path.join(date_dir, filename)
        
        # Get field names from first result
        fieldnames = results[0].keys()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        return output_path
    
    def clear_results(self, search_term=None):
        """Clear results from database, optionally for specific search term"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if search_term:
                cursor.execute("DELETE FROM results WHERE search_term = ?", (search_term,))
            else:
                cursor.execute("DELETE FROM results")
            
            conn.commit()
            
            return cursor.rowcount 