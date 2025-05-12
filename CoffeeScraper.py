import requests
import json
import pandas as pd
import re
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta, timezone
import pytz
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CoffeeScraper.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Script started.")

# Load configuration from config.json
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
try:
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
    iterations = config["iterations"]
    url = config["url"]
    headers = config["headers"]
    query_params = config["query_params"]
    include_keywords = config["filter"]["include_keywords"]
    exclude_keywords = config["filter"]["exclude_keywords"]
    logging.info("Configuration loaded successfully.")
except FileNotFoundError:
    logging.error(f"Configuration file not found: {config_path}")
    raise FileNotFoundError(f"Configuration file not found: {config_path}")
except json.JSONDecodeError as e:
    logging.error(f"Error decoding JSON configuration file: {e}")
    raise ValueError(f"Error decoding JSON configuration file: {e}")
except KeyError as e:
    logging.error(f"Missing required configuration key: {e}")
    raise KeyError(f"Missing required configuration key: {e}")
except Exception as e:
    logging.error(f"Unexpected error while loading configuration: {e}")
    raise Exception(f"Unexpected error while loading configuration: {e}")

# Optional text normalization for descriptions
def normalize(text):
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'\s*\n\s*|<br />|\s+', ' ', text)  # Normalize whitespace and line breaks
    return text

def offersParse(offersJson):
    offers = offersJson['data']
    offersDF = pd.DataFrame(columns=('id', 'url', 'title', 'description', 'promoted', 'promotion_option', 
                                      'created_time', 'last_refresh_time', 'mark', 'price', 
                                      'previous_price', 'currency', 'negotiable', 'condition', 
                                      'city', 'district', 'region', 'latitude', 'longitude', 
                                      'seller', 'photo_url', 'delivery'))

    for offer in offers:
        mark, price, previous_price, currency, negotiable, condition = ["N/A"] * 6
        promoted = False
        promotion_option = []

        if 'promotion' in offer and offer['promotion']:
            promotion = offer['promotion']
            promoted = any([promotion.get('highlighted', False),
                             promotion.get('urgent', False),
                             promotion.get('top_ad', False)])
            promotion_option = promotion.get('options', [])

        if 'partner' in offer and offer['partner'] and offer['partner'].get('code') == 'otomoto_pl_form':
            promotion_option.append('otomoto')

        promotion_type_str = ",".join(promotion_option) if promotion_option else "N/A"
        
        for param in offer['params']:
            if param['key'] == 'brand':
                mark = param['value']['key']
            elif param['key'] == 'price':
                price = param['value']['value']
                previous_price = param['value']['previous_value']
                currency = param['value']['currency']
                negotiable = param['value']['negotiable']
            elif param['key'] == 'state':
                condition = param['value']['key']

        seller = 'company' if offer['business'] else 'private'

        data = {
            "id": offer["id"],
            "url": offer["url"],
            "title": offer["title"],
            "description": normalize(offer["description"]),
            "promoted": promoted,
            "promotion_option": promotion_type_str,
            "created_time": offer["created_time"],
            "last_refresh_time": offer["last_refresh_time"],
            "mark": mark,
            "price": price,
            "previous_price": previous_price,
            "currency": currency,
            "negotiable": negotiable,
            "condition": condition,
            "city": offer["location"]["city"]["name"],
            "district": offer["location"]["district"]["name"] if offer["location"].get("district") else None,
            "region": offer["location"]["region"]["name"],
            "latitude": offer["map"]["lat"],
            "longitude": offer["map"]["lon"],
            "seller": seller,
            "photo_url": re.sub(r";s=\{width\}x\{height\}$", "", offer["photos"][0]["link"]) if offer["photos"] else None,
            "delivery": offer["delivery"]["rock"]["active"]
        }

        offerDF = pd.DataFrame([data])
        offersDF = pd.concat([offerDF, offersDF], ignore_index=True)

    return offersDF

### Main script starts here ###
offers_to_send = pd.DataFrame()
begin_iteration = iterations

payload = ""

df = pd.DataFrame()
fail_counter = 0

while iterations != 0:
    logging.info(f"Starting iteration {begin_iteration - iterations + 1} of {begin_iteration}.")
    query_params["offset"] = iterations * 40  # Update offset dynamically
    r = requests.request("GET", url, data=payload, headers=headers, params=query_params)

    if r.status_code == 200:
        logging.info(f"API request successful for iteration {begin_iteration - iterations + 1}.")
        offer = r.json()
        sub_df = offersParse(offer)
        df = pd.concat([df, sub_df], ignore_index=True)
    else:
        logging.error(f"API request failed with status code {r.status_code} for iteration {begin_iteration - iterations + 1}.")
        fail_counter += 1

    iterations -= 1

logging.info(f"API returned {len(df)} rows in total.")

# Identify and drop duplicate rows on the 'id' column
initial_row_count = len(df)
df = df.drop_duplicates(subset='id', keep=False)
final_row_count = len(df)

if initial_row_count != final_row_count:
    logging.info(f"Removed {initial_row_count - final_row_count} duplicate rows from the DataFrame.")
else:
    logging.info("No duplicate rows found in the DataFrame.")

# Apply include and exclude filters
if include_keywords:
    include_pattern = '|'.join(include_keywords)
    df = df[
        df['title'].str.contains(include_pattern, case=False, na=False) |
        df['description'].str.contains(include_pattern, case=False, na=False)
    ]
    logging.info(f"Filtered offers to include keywords: {include_keywords}")
if exclude_keywords:
    exclude_pattern = '|'.join(exclude_keywords)
    df = df[
        ~df['title'].str.contains(exclude_pattern, case=False, na=False) &
        ~df['description'].str.contains(exclude_pattern, case=False, na=False)
    ]
    logging.info(f"Filtered offers to exclude keywords: {exclude_keywords}")

# Timezone conversion and filtering for the last 7 days
seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
df['created_time'] = pd.to_datetime(df['created_time'], utc=True).dt.tz_convert('Europe/Warsaw')
df['last_refresh_time'] = pd.to_datetime(df['last_refresh_time'], utc=True).dt.tz_convert('Europe/Warsaw')
df = df[df['created_time'] >= seven_days_ago]
df = df.sort_values(by='created_time', ascending=False)

# Define the base directory
base_dir = os.path.dirname(os.path.abspath(__file__))
# Ensure the 'data' folder exists within the main directory
data_dir = os.path.join(base_dir, 'data')
os.makedirs(data_dir, exist_ok=True)
# Ensure the 'database' folder exists within the main directory
database_dir = os.path.join(base_dir, 'database')
os.makedirs(database_dir, exist_ok=True)

# Saving csv backup of the DataFrame
df.to_csv(os.path.join(data_dir, 'OLX_coffeeScrape.csv'))

# DATABASE PART
try:
    conn = sqlite3.connect(os.path.join(database_dir, 'CoffeeOffers_database.db'))
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name='offers';"
    table_exists = pd.read_sql_query(query, conn)

    if not table_exists.empty:
        logging.info("Table 'offers' exists in the database.")
        df_db = pd.read_sql_query("SELECT * FROM offers", conn)
        logging.info(f"Fetched {len(df_db)} rows from the database.")
        existing_ids = df_db['id'].tolist()
        unique_rows = df[~df['id'].isin(existing_ids)]

        if not unique_rows.empty:
            logging.info(f"Found {len(unique_rows)} new unique rows to add to the database.")
            current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            # Create a folder structure based on the current date within the 'data' directory
            folder_path = os.path.join(data_dir, datetime.now().strftime('%Y'), datetime.now().strftime('%m'), datetime.now().strftime('%d'))
            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, f'new_offers_{current_datetime}.csv')
            unique_rows.to_csv(file_path, index=False)
            logging.info(f"Saved new offers to CSV file: {file_path}")
            unique_rows.to_sql('offers', conn, if_exists='append', index=False)
            logging.info("New offers successfully added to the database.")
            offers_to_send = unique_rows
    else:
        logging.info("Table 'offers' does not exist. Creating a new table.")
        df.to_sql('offers', conn, if_exists='replace', index=False)
        logging.info("Database table 'offers' created and data inserted.")
except sqlite3.Error as e:
    logging.error(f"Database error: {e}")
except Exception as e:
    logging.error(f"Unexpected error during database operations: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()
        logging.info("Database connection closed.")

# DUPECHECK
def dupecheck(delete, subset):
    try:
        logging.info("Running duplicate check.")
        conn = sqlite3.connect(os.path.join(database_dir, 'CoffeeOffers_database.db'))
        df_db = pd.read_sql_query("SELECT * FROM offers", conn)
        logging.info(f"Fetched {len(df_db)} rows from the database for duplicate check.")
        duplicate_rows = df_db[df_db.duplicated(subset, keep=False)]

        if not duplicate_rows.empty and delete == False:
            logging.warning(f"Found {len(duplicate_rows)} duplicate rows.")
        elif not duplicate_rows.empty and delete == True:
            logging.info(f"Deleting {len(duplicate_rows)} duplicate rows.")
            df_db = df_db.drop_duplicates(subset='id', keep=False)
            df_db.to_sql('offers', conn, if_exists='replace', index=False)
            logging.info("Duplicate rows successfully deleted from the database.")
    except sqlite3.Error as e:
        logging.error(f"Database error during duplicate check: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during duplicate check: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logging.info("Duplicate check completed and database connection closed.")

dupecheck(delete=True, subset='id')

# Sorting the DataFrame by 'created_time' in descending order
try:
    conn = sqlite3.connect(os.path.join(database_dir, 'CoffeeOffers_database.db'))
    df_db2 = pd.read_sql_query("SELECT * FROM offers", conn)
    df_db2 = df_db2.sort_values(by='created_time', ascending=False)
    df_db2.to_sql('offers', conn, if_exists='replace', index=False)
except sqlite3.Error as e:
    logging.error(f"Database error during sorting: {e}")
except Exception as e:
    logging.error(f"Unexpected error during sorting: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()

def validate_email(email):
    """Validate email format."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

# Read sensitive information from environment variables
sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")
recipient_email = os.getenv("RECIPIENT_EMAIL")

# Validate environment variables
if not validate_email(sender_email):
    logging.error("Invalid sender email format.")
    raise ValueError("Invalid sender email format.")
if not validate_email(recipient_email):
    logging.error("Invalid recipient email format.")
    raise ValueError("Invalid recipient email format.")
if not sender_password:
    logging.error("Sender password is missing.")
    raise ValueError("Sender password is missing.")

subject_template = "New Offer: {title}"
body_template = """\
Tytuł: {title}
Opis: {description}

Cena: {price} {currency}{previous_price}
Lokalizacja: {city}{district_info}, {region}
Stan: {condition}
URL: {url}
Wysyłka OLX: {delivery}
Sprzedawca: {seller_type}
Data dodania: {created_time}
"""

def send_email(sender_email, sender_password, recipient_email, subject, body, attachments=None, retries=3):
    """
    Sends an email with optional attachments and retry logic.

    :param sender_email: Sender's email address.
    :param sender_password: Sender's email password.
    :param recipient_email: Recipient's email address.
    :param subject: Email subject.
    :param body: Email body.
    :param attachments: List of tuples (filename, filedata) for attachments.
    :param retries: Number of retry attempts in case of failure.
    """
    masked_email = recipient_email[:2] + "****" + recipient_email.split("@")[-1]  # Mask email for logging
    for attempt in range(retries):
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Attach files if provided
            if attachments:
                for filename, filedata in attachments:
                    from email.mime.base import MIMEBase
                    from email import encoders

                    attachment = MIMEBase('application', 'octet-stream')
                    attachment.set_payload(filedata)
                    encoders.encode_base64(attachment)
                    attachment.add_header('Content-Disposition', f'attachment; filename={filename}')
                    msg.attach(attachment)

            # Send the email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            logging.info(f"Email sent successfully to {masked_email}.")
            return  # Exit the function if email is sent successfully
        except smtplib.SMTPAuthenticationError:
            logging.error("SMTP authentication failed. Check your email credentials.")
            raise
        except smtplib.SMTPException as e:
            logging.error(f"SMTP error occurred: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while sending email: {e}")
            raise

def send_email_for_each_row(sender_email, sender_password, recipient_email, subject_template, body_template, data):
    """
    Sends an email for each row in the provided DataFrame.

    :param sender_email: Sender's email address.
    :param sender_password: Sender's email password.
    :param recipient_email: Recipient's email address.
    :param subject_template: Template for the email subject.
    :param body_template: Template for the email body.
    :param data: DataFrame containing the data to include in the emails.
    """
    for index, row in data.iterrows():
        subject = subject_template.format(title=row['title'])
        seller_type = "Firma" if row['seller'] == 'company' else "Prywatny"
        condition = 'Nowy' if row['condition'] == 'new' else 'Używany' if row['condition'] == 'used' else 'Uszkodzony'

        body = body_template.format(
            title=row['title'],
            description=row['description'],
            price=row['price'],
            previous_price=f' | Wcześniej: {row["previous_price"]} {row["currency"]}' if pd.notna(row['previous_price']) else "",
            currency=row['currency'],
            city=row['city'],
            district_info=f" {row['district']}" if pd.notna(row['district']) else "",
            region=row['region'],
            condition=condition,
            url=row['url'],
            photo_url=row['photo_url'],
            delivery='Tak' if row['delivery'] == True else 'Nie',
            created_time=row['created_time'].strftime('%Y-%m-%d %H:%M:%S'),
            seller_type=seller_type
        )

        # Fetch image for attachment
        attachments = []
        try:
            response = requests.get(row['photo_url'], stream=True)
            if response.status_code == 200:
                img_data = response.content
                img_name = f"image_{index}.jpg"
                attachments.append((img_name, img_data))
        except Exception as e:
            logging.error(f"Error fetching image for row {index}: {e}")

        # Send email
        send_email(sender_email, sender_password, recipient_email, subject, body, attachments)

send_emails = True

if not offers_to_send.empty:
    data = offers_to_send.reset_index(drop=True).reset_index()
    try:
        send_email_for_each_row(sender_email, sender_password, recipient_email, subject_template, body_template, data=data)
        logging.info("Emails sent successfully.")
    except Exception as e:
        logging.error(f"Error while sending emails: {e}")
else:
    logging.info("No new offers found. No emails were sent.")

logging.info("Script finished.")