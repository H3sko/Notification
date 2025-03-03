import smtplib
import ssl
import json
import requests
# AWS
# import boto3
from email.message import EmailMessage
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from credentials import Constants as Credentials



def gymbeam_notification():
    soup = get_soup("https://gymbeam.sk")
    soup2 = get_soup("https://gymbeam.sk/protein-wpc-80-gymbeam.html")

    protein_price = float(soup2.find('span', class_='price').get_text(strip=True).replace('€', '').replace(',', '.').replace(' ', '').replace('\xa0', ''))
    max_price = 17.00
    
    wordbank = ['zlavy', 'zľavy']
    sales = any(word in soup.get_text().lower() for word in wordbank)

    sent = False

    if sales:
        try:
            send_email(source='Gymbeam', title=['ZLAVY'], content=[])
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Error sending email'})
            }
        else:
            sent = True
    elif protein_price < max_price:
        try:
            send_email(source='Gymbeam', title=[f'1kg whey protein = {protein_price}€'], content=[])
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Error sending email'})
            }
        else:
            sent = True

    if sent:
        return {
                'statusCode': 200,
                'body': json.dumps('Email sent successfully')    
        }
    else:
        return {
                'statusCode': 204,
                'body': json.dumps('Email not sent because there were no new listings')
            }

    
        

# ------------------------------------------------------------------------------------------------------------------------------------------------------

def fetch_book_publisher(link):
    try:
        re_book = requests.get(link)
        soup_book = BeautifulSoup(re_book.content, "html.parser")
        publisher = soup_book.find('tr', class_='woocommerce-product-attributes-item woocommerce-product-attributes-item--attribute_pa_vydavatelstvo-rok').find('td', class_='woocommerce-product-attributes-item__value').get_text(strip=True).lower()
        return publisher
    except Exception as e:
        print(f"Error fetching publisher for {link}: {e}")
        return None

def antikvariatjusticna_notification():
    publishers = ["Absynt", "N Press", "Hadart", "Artforum", "Premedia"]

    soup_page1 = get_soup("https://www.antikvariatjusticna.sk/obchod/?orderby=date&v=13dd621f2711")
    soup_page2 = get_soup("https://www.antikvariatjusticna.sk/obchod/page/2/?orderby=date&v=13dd621f2711")

    books = soup_page1.findAll('a', class_='woocommerce-LoopProduct-link woocommerce-loop-product__link') + soup_page2.findAll('a', class_='woocommerce-LoopProduct-link woocommerce-loop-product__link')
    links = [book.get('href') for book in books]

    filtered_items = []
    filtered_publishers = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_book_publisher, links)

    for link, publisher in zip(links, results):
        if publisher is not None:
            for p in publishers:
                if p.lower() in publisher.lower():
                    filtered_publishers.append(p)
                    filtered_items.append(link)

    filtered_items_final = []
    filtered_publishers_final = []

    # Open file to read and write saved IDs
    # AWS
    """
    s3_client = boto3.client('s3')
    
    bucket = "notification-data-bucket"
    key = "data.txt"
    filepath = "/tmp/" + key
    
    s3_client.download_file(bucket, key, filepath)
    """
    # AWS
    if len(filtered_items) == len(filtered_publishers):
        with open('data.txt', 'r+') as file:
            saved_links = {line.strip() for line in file}
            for item, publisher in zip(filtered_items, filtered_publishers):
                if item not in saved_links:
                    filtered_items_final.append(item)
                    filtered_publishers_final.append(publisher)
                    file.write("\n" + item)

    try:
        if len(filtered_items_final) > 0:
            send_email(source='AntikvariatJusticna', title=filtered_publishers_final, content=filtered_items_final)
        else:
            return {
                'statusCode': 204,
                'body': json.dumps('Email not sent because there were no new listings')
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error sending email'})
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('Email sent successfully')    
        }

# ------------------------------------------------------------------------------------------------------------------------------------------------------

def mtbiker_notification():
    # Brands of interest
    brands = ("Specialized", "S Works", "S-Works", "SWorks", "Canyon", "Basso", 
              "DeRosa", "De Rosa", "Bianchi", "Wilier", "Colnago", "Pinarello", 
              "BMC", "Cervelo", "Cannondale", "Canonndale", "Canondale", "Cinelli", 
              "Scott", "Trek", "Cinelli", "Bottecchia", "Passoni", "Guerciotti", 
              "Tommasini", "Daccorrdi")
    
    bottom_price = 450
    top_price = 2501
    
    # Lists to store filtered items and IDs
    filtered_ids = []
    filtered_items = []
    filtered_brands = []
    
    # Open file to read and write saved IDs
    # AWS
    """
    s3_client = boto3.client('s3')
    
    bucket = "notification-data-bucket"
    key = "data.txt"
    filepath = "/tmp/" + key
    
    s3_client.download_file(bucket, key, filepath)
    """
    # AWS
    with open('data.txt', 'r+') as file:
        saved_ids = {line.strip() for line in file}

        soup = get_soup("https://www.mtbiker.sk/?modul=bazar&_route_=bicykle/cestne")
        soup2 = get_soup("https://www.mtbiker.sk/bazar/bicykle/cestne?modul=bazar&od=2")

        # Combine items from both pages
        bazaar_items = soup.find_all('div', class_='bazaar-item')[1:] + soup2.find_all('div', class_='bazaar-item')[1:]

        for item in bazaar_items:
            # Extract ID, badge value, and country
            item_id = item.get('id').split('-')[-1]
            badge_value = int(item.find('span', class_='badge badge-dark mr-1').get_text(strip=True).replace('€', '').replace('Kč', '').replace(' ', '').replace('\xa0', ''))

            # Check conditions
            if item_id not in saved_ids and bottom_price <= badge_value <= top_price:
                title = item.find('a', class_='link-dark').get_text(strip=True).lower()
                description = item.find('div', class_='bazaar-item-perex').get_text(strip=True).lower()
                for brand in brands:
                    if brand.lower() in title and 'sram' not in description:
                        # Add item to filtered_items
                        filtered_ids.append(item_id)
                        filtered_items.append(item.find('a', class_='link-dark')['href'])
                        # Add brandname to filtered_brands
                        filtered_brands.append(brand)
                        # Write item ID to file
                        file.write("\n" + item_id)
                        break
       

    # AWS
    # s3_client.upload_file(filepath, bucket, key)

    try:
        if len(filtered_items) > 0:
            send_email(source='MTBiker', title=filtered_brands, content=filtered_items)
        else:
            return {
                'statusCode': 204,
                'body': json.dumps('Email not sent because there were no new listings')
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error sending email'})
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('Email sent successfully')    
        }
    
# ------------------------------------------------------------------------------------------------------------------------------------------------------

def status_notification():
    try:
        send_email(source='Status update', brands=['running'], items=[])
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error sending email'})
        }
    else:
        return {
            'statusCode': 200,
            'body': json.dumps('Email sent successfully')    
        }

# ------------------------------------------------------------------------------------------------------------------------------------------------------

def send_email(source: str, title: list, content: list):
    # Set up SMTP server
    smtp_server = 'smtp.gmail.com'
    port = 587
    sender_email = Credentials.email
    receiver_email = Credentials.email
    password = Credentials.password

    # Compose email message
    message = EmailMessage()
    message['From'] = sender_email
    message['To'] = receiver_email

    # Set up subject with joined brands
    if (len(title) == len(content)):
        message['Subject'] = f'{source} ({len(title)}) : {", ".join(title)}'
    else:
        message['Subject'] = f'{source} : {", ".join(title)}'

    # Set up content with joined items
    text = "\n\n".join(content)
    message.set_content(text)

    context = ssl.create_default_context()

    # Send email
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.send_message(message)

# ------------------------------------------------------------------------------------------------------------------------------------------------------

def get_soup(url):
    """Get BeautifulSoup object from a given URL."""
    page = requests.get(url)
    return BeautifulSoup(page.content, "html.parser")