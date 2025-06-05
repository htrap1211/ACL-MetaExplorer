# ACL Anthology Paper Metadata Explorer

## Project Description

This project is an interactive tool for exploring and analyzing academic paper metadata from the ACL Anthology. It provides functionalities for processing paper data (specifically, extracting keywords), storing it in a structured database, and visualizing trends and information through a Streamlit dashboard.

The primary goal is to make the wealth of information in the ACL Anthology accessible and explorable, allowing users to filter papers, view details, and analyze keyword trends over time.

## Features

- **Data Processing:** Scripts to process raw paper data, including keyword extraction.
- **Keyword Extraction:** Utilizes techniques like RAKE and spaCy to extract relevant keywords from paper titles and abstracts.
- **Data Storage:** Stores structured paper metadata (including extracted keywords) in a SQLite database for efficient querying.
- **Data Synchronization:** A script to sync processed data from JSON files into the SQLite database.
- **Interactive Dashboard:** A Streamlit web application offering:
    - **Paper Explorer:** Browse, filter, and search papers by title, year, and keywords.
    - **Trend Analysis:** Visualize keyword trends and perform TF-IDF analysis on paper abstracts over different periods (currently by year).

## Data

The project uses academic paper metadata sourced from the ACL Anthology. The scraped data is initially stored as JSON files in the `data/json` directory.
A SQLite database (`data/academic_metadata.db`) is used to store a structured version of this data for faster querying by the dashboard.

## Installation

To set up the project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd Text_technology
    ```
    *(Replace `<repository_url>` with the actual URL of your repository)*

2.  **Create and activate a virtual environment:**
    It's recommended to use a virtual environment to manage dependencies.
    ```bash
    python -m venv venv
    # On macOS/Linux:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```

3.  **Install dependencies:**
    Install the required Python packages using the provided `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download spaCy model:**
    The keyword extraction process requires a spaCy English model.
    ```bash
    python -m spacy download en_core_web_sm
    ```

## Usage

Follow these steps to process the data and run the dashboard:

1.  **Ensure you have the data:**
    Make sure your ACL Anthology paper data is in the `data/json` directory. Data for the years 2010-2024 should already be present if you followed previous steps, but you might need to run scraping scripts if you extend the date range.

2.  **Extract Keywords:**
    Run the script to add keywords to your JSON data. You've likely already done this.
    ```bash
    python src/process/add_keywords.py
    ```

3.  **Sync data to the SQLite database:**
    Run the synchronization script to load the data from JSON files (including the newly added keywords) into the SQLite database.
    ```bash
    python src/access/sync_json_to_db.py
    ```

4.  **Run the Streamlit Dashboard:**
    Start the interactive dashboard application.
    ```bash
    streamlit run src/access/streamlit_dashboard.py
    ```
    Open your web browser and go to the local URL provided by Streamlit (usually `http://localhost:8501`).

## Project Structure

- `data/`: Contains raw JSON data (`data/json/`) and the SQLite database (`data/academic_metadata.db`).
- `src/`: Contains the project's source code.
    - `process/`: Scripts for data processing (e.g., `add_keywords.py`).
    - `access/`: Scripts for data access and the dashboard (`streamlit_dashboard.py`, `sync_json_to_db.py`).
    - `utils/`: Utility scripts (e.g., `clean_text.py`).
