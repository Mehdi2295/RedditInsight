import sys
import os
import threading
import webbrowser
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QFileDialog,
    QCheckBox, QMessageBox, QProgressBar, QGroupBox, QSplitter,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QDesktopServices, QColor

from scraper import RedditScraper
from database import Database
from processor import Processor

class ScraperSignals(QObject):
    """Signals to communicate between threads"""
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

class ScraperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.db = Database()
        self.processor = Processor()
        self.reddit_scraper = RedditScraper()
        self.signals = ScraperSignals()
        
        # Setup UI
        self.setWindowTitle("Social Media Content Scraper")
        self.setGeometry(100, 100, 1200, 800)
        
        self.init_ui()
        
        # Connect signals
        self.signals.progress.connect(self.update_progress)
        self.signals.message.connect(self.update_status)
        self.signals.finished.connect(self.handle_scrape_complete)
        self.signals.error.connect(self.handle_error)
        
    def init_ui(self):
        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Search section
        search_group = QGroupBox("Search")
        search_layout = QVBoxLayout()
        
        # Search input
        search_input_layout = QHBoxLayout()
        search_input_layout.addWidget(QLabel("Search Term:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter software name or keyword...")
        search_input_layout.addWidget(self.search_input)
        
        # Timeframe dropdown
        search_input_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["All Time", "Last Week", "Last Month", "Last Year"])
        search_input_layout.addWidget(self.timeframe_combo)
        
        # Source checkboxes
        self.reddit_checkbox = QCheckBox("Reddit")
        self.reddit_checkbox.setChecked(True)
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Sources:"))
        source_layout.addWidget(self.reddit_checkbox)
        source_layout.addStretch()
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.start_scraping)
        search_input_layout.addWidget(self.search_button)
        
        # Progress bar and status
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        # Add all to search layout
        search_layout.addLayout(search_input_layout)
        search_layout.addLayout(source_layout)
        search_layout.addLayout(progress_layout)
        search_group.setLayout(search_layout)
        
        # Main content area with tabs
        self.tabs = QTabWidget()
        
        # Results tab
        self.results_tab = QWidget()
        results_layout = QVBoxLayout()
        
        # Split view for results list and content preview
        results_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_result_details)
        results_splitter.addWidget(self.results_list)
        
        # Result details
        result_details_widget = QWidget()
        result_details_layout = QVBoxLayout()
        
        self.result_title = QLabel("Select a result to view details")
        self.result_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        result_details_layout.addWidget(self.result_title)
        
        result_meta_layout = QHBoxLayout()
        self.result_source = QLabel("")
        self.result_date = QLabel("")
        result_meta_layout.addWidget(self.result_source)
        result_meta_layout.addWidget(self.result_date)
        result_meta_layout.addStretch()
        
        self.result_url = QLabel("")
        self.result_url.setOpenExternalLinks(True)
        
        self.result_content = QTextEdit()
        self.result_content.setReadOnly(True)
        
        result_details_layout.addLayout(result_meta_layout)
        result_details_layout.addWidget(self.result_url)
        result_details_layout.addWidget(self.result_content)
        
        result_details_widget.setLayout(result_details_layout)
        results_splitter.addWidget(result_details_widget)
        
        # Set initial sizes
        results_splitter.setSizes([300, 700])
        
        results_layout.addWidget(results_splitter)
        
        # Export buttons
        export_layout = QHBoxLayout()
        self.export_json_button = QPushButton("Export to JSON")
        self.export_json_button.clicked.connect(self.export_to_json)
        self.export_csv_button = QPushButton("Export to CSV")
        self.export_csv_button.clicked.connect(self.export_to_csv)
        export_layout.addWidget(self.export_json_button)
        export_layout.addWidget(self.export_csv_button)
        export_layout.addStretch()
        
        results_layout.addLayout(export_layout)
        self.results_tab.setLayout(results_layout)
        
        # Analysis tab
        self.analysis_tab = QWidget()
        analysis_layout = QVBoxLayout()
        
        self.analyze_button = QPushButton("Generate Analysis")
        self.analyze_button.clicked.connect(self.generate_analysis)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        
        analysis_layout.addWidget(self.analyze_button)
        analysis_layout.addWidget(self.analysis_text)
        
        self.analysis_tab.setLayout(analysis_layout)
        
        # History tab
        self.history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        self.history_list = QTableWidget()
        self.history_list.setColumnCount(3)
        self.history_list.setHorizontalHeaderLabels(["Search Term", "Timeframe", "Date"])
        self.history_list.horizontalHeader().setStretchLastSection(True)
        self.history_list.itemDoubleClicked.connect(self.load_from_history)
        
        self.refresh_history_button = QPushButton("Refresh History")
        self.refresh_history_button.clicked.connect(self.load_history)
        
        history_layout.addWidget(self.history_list)
        history_layout.addWidget(self.refresh_history_button)
        
        self.history_tab.setLayout(history_layout)
        
        # Add tabs
        self.tabs.addTab(self.results_tab, "Results")
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.addTab(self.history_tab, "History")
        
        # Add components to main layout
        main_layout.addWidget(search_group)
        main_layout.addWidget(self.tabs)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Load initial data
        self.load_history()
    
    def start_scraping(self):
        """Start the scraping process in a separate thread"""
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "Input Error", "Please enter a search term.")
            return
        
        timeframe_mapping = {
            "All Time": "all",
            "Last Week": "week",
            "Last Month": "month",
            "Last Year": "year"
        }
        timeframe = timeframe_mapping[self.timeframe_combo.currentText()]
        
        sources = []
        if self.reddit_checkbox.isChecked():
            sources.append("reddit")
            
        if not sources:
            QMessageBox.warning(self, "Input Error", "Please select at least one source.")
            return
        
        # Clear previous results
        self.results_list.clear()
        self.update_result_details(None)
        
        # Reset progress and status
        self.progress_bar.setValue(0)
        self.update_status(f"Starting search for '{keyword}'...")
        
        # Disable search button
        self.search_button.setEnabled(False)
        
        # Start scraping thread
        scrape_thread = threading.Thread(
            target=self.run_scraping, 
            args=(keyword, timeframe, sources)
        )
        scrape_thread.daemon = True
        scrape_thread.start()
    
    def run_scraping(self, keyword, timeframe, sources):
        """Run the scraping process (called in separate thread)"""
        try:
            all_results = []
            
            # Track progress
            total_sources = len(sources)
            source_progress = 0
            
            if "reddit" in sources:
                self.signals.message.emit(f"Searching Reddit for '{keyword}'...")
                reddit_results = self.reddit_scraper.search(keyword, timeframe)
                all_results.extend(reddit_results)
                source_progress += 1
                self.signals.progress.emit(int(source_progress / total_sources * 100))
                self.signals.message.emit(f"Found {len(reddit_results)} results from Reddit")
            
            # Save results to database
            self.db.save_results(all_results, keyword)
            self.db.save_search(keyword, timeframe)
            
            self.signals.message.emit(f"Search complete. Found {len(all_results)} results.")
            self.signals.finished.emit(all_results)
            
        except Exception as e:
            self.signals.error.emit(f"Error during scraping: {str(e)}")
            
        finally:
            # Re-enable search button
            self.search_button.setEnabled(True)
    
    def handle_scrape_complete(self, results):
        """Handle when scraping is complete"""
        self.progress_bar.setValue(100)
        self.search_button.setEnabled(True)
        
        # Format results for display
        formatted_results = self.processor.format_results_for_display(results)
        
        # Add to results list
        self.results_list.clear()
        for result in formatted_results:
            item = QListWidgetItem(f"{result['title']} ({result['source']})")
            item.setData(Qt.ItemDataRole.UserRole, result)
            self.results_list.addItem(item)
        
        # Update history tab
        self.load_history()
        
        # Switch to results tab
        self.tabs.setCurrentIndex(0)
    
    def show_result_details(self, item):
        """Show details of the selected result"""
        result = item.data(Qt.ItemDataRole.UserRole)
        self.update_result_details(result)
    
    def update_result_details(self, result):
        """Update the result details panel"""
        if result is None:
            self.result_title.setText("Select a result to view details")
            self.result_source.setText("")
            self.result_date.setText("")
            self.result_url.setText("")
            self.result_content.setText("")
            return
        
        self.result_title.setText(result['title'])
        self.result_source.setText(f"Source: {result['source']} / {result['community']}")
        
        # Format date if available
        date_str = ""
        if result['date']:
            try:
                date_obj = datetime.fromisoformat(result['date'])
                date_str = date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = result['date']
        
        self.result_date.setText(f"Date: {date_str}")
        
        # Set URL as clickable link
        url = result['url']
        self.result_url.setText(f"<a href='{url}'>{url}</a>")
        
        # Set content
        full_result = result.get('full_result', {})
        content = full_result.get('content', result.get('content', ''))
        self.result_content.setText(content)
    
    def export_to_json(self):
        """Export results to JSON file in the organized folder structure"""
        search_term = self.search_input.text().strip()
        if not search_term:
            QMessageBox.warning(self, "Export Error", "No search term specified.")
            return
        
        # Use the updated export function that creates folders automatically
        output_path = self.db.export_results_to_json(search_term)
        
        if output_path:
            QMessageBox.information(
                self, "Export Complete", 
                f"Results exported to {output_path}"
            )
    
    def export_to_csv(self):
        """Export results to CSV file in the organized folder structure"""
        search_term = self.search_input.text().strip()
        if not search_term:
            QMessageBox.warning(self, "Export Error", "No search term specified.")
            return
        
        # Use the updated export function that creates folders automatically
        output_path = self.db.export_results_to_csv(search_term)
        
        if output_path:
            QMessageBox.information(
                self, "Export Complete", 
                f"Results exported to {output_path}"
            )
        else:
            QMessageBox.warning(
                self, "Export Error", 
                "No results found to export."
            )
    
    def generate_analysis(self):
        """Generate analysis of current results"""
        search_term = self.search_input.text().strip()
        if not search_term:
            QMessageBox.warning(self, "Analysis Error", "No search term specified.")
            return
        
        # Get results from database
        results = self.db.get_results(search_term=search_term)
        
        if not results:
            QMessageBox.warning(
                self, "Analysis Error", 
                "No results found for analysis."
            )
            return
        
        # Run analysis
        analysis = self.processor.analyze_results(results)
        
        # Generate report
        report = self.processor.generate_text_report(analysis, search_term)
        
        # Display in analysis tab
        self.analysis_text.setText(report)
        
        # Switch to analysis tab
        self.tabs.setCurrentIndex(1)
    
    def load_history(self):
        """Load search history from database"""
        history = self.db.get_search_history()
        
        self.history_list.setRowCount(len(history))
        
        for i, entry in enumerate(history):
            search_term_item = QTableWidgetItem(entry.get('search_term', ''))
            timeframe_item = QTableWidgetItem(entry.get('timeframe', ''))
            
            # Format timestamp
            timestamp = entry.get('timestamp', '')
            if timestamp:
                try:
                    date_obj = datetime.fromisoformat(timestamp)
                    timestamp = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            timestamp_item = QTableWidgetItem(timestamp)
            
            self.history_list.setItem(i, 0, search_term_item)
            self.history_list.setItem(i, 1, timeframe_item)
            self.history_list.setItem(i, 2, timestamp_item)
        
        self.history_list.resizeColumnsToContents()
    
    def load_from_history(self, item):
        """Load a search from history"""
        row = item.row()
        search_term = self.history_list.item(row, 0).text()
        timeframe = self.history_list.item(row, 1).text()
        
        # Set search term
        self.search_input.setText(search_term)
        
        # Set timeframe
        timeframe_mapping = {
            "all": "All Time",
            "week": "Last Week",
            "month": "Last Month",
            "year": "Last Year"
        }
        if timeframe in timeframe_mapping:
            index = self.timeframe_combo.findText(timeframe_mapping[timeframe])
            if index >= 0:
                self.timeframe_combo.setCurrentIndex(index)
        
        # Load results
        results = self.db.get_results(search_term=search_term)
        formatted_results = self.processor.format_results_for_display(results)
        
        # Display results
        self.results_list.clear()
        for result in formatted_results:
            item = QListWidgetItem(f"{result['title']} ({result['source']})")
            item.setData(Qt.ItemDataRole.UserRole, result)
            self.results_list.addItem(item)
        
        # Switch to results tab
        self.tabs.setCurrentIndex(0)
        
        # Show status message
        self.update_status(f"Loaded {len(results)} results for '{search_term}'")
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.setText(message)
    
    def handle_error(self, error_message):
        """Handle error from scraping thread"""
        QMessageBox.critical(self, "Error", error_message)
        self.search_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.update_status("Error occurred. Please try again.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScraperApp()
    window.show()
    sys.exit(app.exec()) 