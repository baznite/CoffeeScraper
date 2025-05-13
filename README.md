# Coffee Scraper v2.0

## Overview
Coffee Scraper v2.0 is a Python application designed to scrape coffee machines offers from the www.olx.pl platform. The application retrieves data through the OLX API, processes the offers, and stores them in a SQLite database. It also provides functionality to send email notifications for new offers.

## Features
- Scrapes offers from the OLX API.
- Normalizes and processes the scraped data.
- Stores offers in a SQLite database.
- Sends email notifications for new offers.
- Generates a CSV backup of the scraped data.
- Filters offers based on keywords and price.

## Project Structure
```
CoffeeScraper_v2.0
├── CoffeeScraper_v2.0.py           # Main script for the Coffee Scraper application
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
The application uses environment variables for configuration. Create a `.env` file in the root directory with the following content:

```
# Email configuration
SENDER_EMAIL=your_email@example.com
SENDER_PASSWORD=your_email_password
RECIPIENT_EMAIL=recipient_email@example.com

# Scraper configuration
CONFIG_ITERATIONS=5
CONFIG_URL=https://www.olx.pl/api/v1/offers/
CONFIG_HEADERS_USER_AGENT=
CONFIG_QUERY_PARAMS_OFFSET=0
CONFIG_QUERY_PARAMS_LIMIT=40
CONFIG_QUERY_PARAMS_CATEGORY_ID=2225
CONFIG_QUERY_PARAMS_FILTER_REFINERS=spell_checker
CONFIG_QUERY_PARAMS_SL=19189988bb7x4bc8e1e7
CONFIG_FILTER_INCLUDE_KEYWORDS=
CONFIG_FILTER_EXCLUDE_KEYWORDS=Uszkodzony
CONFIG_MAX_PRICE=500

# Logging configuration
LOGGING_LEVEL=DEBUG
```

- `SENDER_EMAIL`, `SENDER_PASSWORD`, and `RECIPIENT_EMAIL` are used for sending email notifications.
- `CONFIG_ITERATIONS` specifies the number of API request iterations.
- `CONFIG_URL` is the base URL for the OLX API.
- `CONFIG_HEADERS_USER_AGENT` specifies the User-Agent header for API requests.
- `CONFIG_QUERY_PARAMS_*` defines the query parameters for the API requests.
- `CONFIG_FILTER_INCLUDE_KEYWORDS` and `CONFIG_FILTER_EXCLUDE_KEYWORDS` define keywords to include or exclude offers based on the `title` or `description`.
- `CONFIG_MAX_PRICE` specifies the maximum price for filtering offers.
- `LOGGING_LEVEL` specifies the logging level for the script. Possible values are `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`. Default is `DEBUG`.

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