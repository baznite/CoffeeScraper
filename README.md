# Coffee Scraper v2.0

## Overview
Coffee Scraper v2.0 is a Python application designed to scrape coffee machines offers from www.olx.pl. The application retrieves data through the OLX API, processes the offers, and stores them in a SQLite database. It also provides functionality to send email notifications for new offers and config file for http request and filtering of response offers.

## Features
- Scrapes offers from the OLX API.
- Normalizes and processes the scraped data.
- Stores offers in a SQLite database.
- Sends email notifications for new offers.
- Generates a CSV backup of the scraped data.

## Project Structure
```
CoffeeScraper_v2.0
├── CoffeeScraper.py                # Main script for the Coffee Scraper application
├── config.json                     # Configuration file for the application
├── data
│   └── OLX_coffeeScrape.csv        # CSV backup of the scraped data
├── database
│   └── CoffeeOffers_database.db    # SQLite database storing the offers
├── requirements.txt                # Lists dependencies required for the project
└── README.md                       # Documentation for the project
```

## Installation
1. Clone the repository or download the project files.
2. Navigate to the project directory.
3. Install the required dependencies using pip:
   ```
   pip install -r requirements.txt
   ```

## Configuration
1. Create a `config.json` file in the root directory with the following structure:
   ```json
   {
       "iterations": 5,
       "url": "https://www.olx.pl/api/v1/offers/",
       "headers": {
           "User-Agent": ""
       },
       "query_params": {
           "offset": 0,
           "limit": "40",
           "category_id": "1776",
           "filter_refiners": "spell_checker",
           "sl": "19189988bb7x4bc8e1e7"
       },
       "filter": {
           "include_keywords": ["Ekspres"],
           "exclude_keywords": ["Uszkodzony", "Zepsuty"]
       }
   }
   ```
   - `iterations`: Number of API request iterations.
   - `url`: Base URL for the OLX API.
   - `headers`: HTTP headers for the API requests.
   - `query_params`: Query parameters for the API requests.
   - `filter`: Keywords to include or exclude offers based on the `title` or `description`.

2. Create a `.env` file in the root directory to store sensitive information:
   ```
   SENDER_EMAIL=your_email@example.com
   SENDER_PASSWORD=your_email_password
   RECIPIENT_EMAIL=recipient_email@example.com
   ```

## Usage
1. Run the main script to start scraping offers:
   ```
   python CoffeeScraper.py
   ```
2. The application will scrape the latest offers, process the data, and store it in the SQLite database.
3. Check the `data/OLX_coffeeScrape.csv` file for a backup of the scraped offers.
4. Email notifications will be sent for any new offers found.

## Contributing
Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## License
This project is licensed under the MIT License.