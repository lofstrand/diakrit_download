import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
import argparse
import sys
import concurrent.futures
from tqdm import tqdm
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

def parse_arguments():
    """
    Parses command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.

    Examples:
    1. Download .jpg Images with All Query Parameters
        `python download_images.py 13011948`
        * Behavior: Downloads all .jpg images associated with orderId=13011948, including all query parameters.
        * Output Directory: downloaded_images

    2. Download .jpg and .png Images, Removing watermark and width
        `python download_images.py 13011948 -e .jpg .png --raw_image --no_watermark`
        * Behavior: Downloads both .jpg and .png images, removing width, height, and watermark from the URLs.
        * Output Directory: downloaded_images

    3. Download Images to a Custom Directory with Parallel Downloads and Logging
        `python download_images.py 13011948 -e .jpg .png --raw_image --no_watermark -o my_images -p -l`
        * Behavior: Downloads images as specified, saves them to my_images, enables parallel downloading, and logs activities.
        * Output Directory: my_images
        * Logging: Enabled (image_downloader.log)

    4. Remove Additional Query Parameters
        `python download_images.py 13011948 -e .jpg .png --remove_params foo bar`
        * Behavior: Downloads .jpg and .png images, removing foo and bar query parameters from the URLs.
        * Output Directory: downloaded_images
    """
    parser = argparse.ArgumentParser(
        description='Download images from Diakrit backend based on order ID.'
    )
    parser.add_argument('order_id', type=int, help='The order ID to fetch images for.')
    parser.add_argument('-e', '--extensions', nargs='+', default=['.jpg'],
                        help='List of image file extensions to download (e.g., .jpg .png). Default is .jpg')
    parser.add_argument('-o', '--output', default='downloaded_images',
                        help='Directory to save downloaded images. Default is "downloaded_images".')
    parser.add_argument('-b', '--base_url', default='https://portal.diakrit.com',
                        help='Base URL of the Diakrit portal. Default is "https://portal.diakrit.com".')
    parser.add_argument('-rp', '--remove_params', nargs='*', default=None,
                        help='List of additional query parameters to remove from image URLs (e.g., foo bar).')
    parser.add_argument('--raw_image', action='store_true',
                        help='Remove both width and height query parameters from image URLs.')
    parser.add_argument('--no_watermark', action='store_true',
                        help='Remove the watermark query parameter from image URLs.')
    parser.add_argument('-p', '--parallel', action='store_true',
                        help='Enable parallel downloads using multithreading.')
    parser.add_argument('-l', '--log', action='store_true',
                        help='Enable logging to a file "image_downloader.log".')
    return parser.parse_args()

def get_page_url(base_url, order_id):
    """
    Constructs the full page URL based on base URL and order ID.

    Args:
        base_url (str): The base URL of the Diakrit portal.
        order_id (int): The order ID to fetch images for.

    Returns:
        str: The complete page URL.
    """
    return f"{base_url}/backend/general/photos/seller?orderid={order_id}"

def get_html_content(url, headers):
    """
    Fetches HTML content from the specified URL.

    Args:
        url (str): The URL to fetch HTML content from.
        headers (dict): HTTP headers to include in the request.

    Returns:
        str: The fetched HTML content as a string. Returns an empty string on failure.
    """
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching HTML from URL: {e}")
        return ""

def extract_image_urls(html, base_url, extensions, remove_params):
    """
    Parses HTML to extract all unique image URLs with specified extensions,
    removing specified query parameters.

    Args:
        html (str): The HTML content to parse.
        base_url (str): The base URL to construct full image URLs.
        extensions (list): List of file extensions to filter images.
        remove_params (dict): Dictionary indicating which parameters to remove.
            Keys can include 'raw_image', 'no_watermark', and 'additional_params'.

    Returns:
        list: A list of cleaned, full image URLs.
    """
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = set()

    # Normalize extensions to lowercase for case-insensitive matching
    extensions = [ext.lower() for ext in extensions]

    # Iterate over all <a> tags with an href attribute
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Check if the href contains '/orderfiles/'
        if '/orderfiles/' in href:
            parsed_url = urlparse(href)
            # Check if the path ends with one of the specified extensions
            if any(parsed_url.path.lower().endswith(ext) for ext in extensions):
                # Parse existing query parameters into a dictionary
                query_dict = parse_qs(parsed_url.query)

                # Remove 'width' and 'height' if raw_image flag is set
                if remove_params.get('raw_image'):
                    query_dict.pop('width', None)
                    query_dict.pop('height', None)

                # Remove 'watermark' if no_watermark flag is set
                if remove_params.get('no_watermark'):
                    query_dict.pop('watermark', None)

                # Remove any additional parameters specified via --remove_params
                for param in remove_params.get('additional_params', []):
                    query_dict.pop(param, None)

                # Reconstruct query string
                new_query = urlencode(query_dict, doseq=True)

                # Reconstruct the URL without the specified query parameters
                clean_url = urlunparse((
                    parsed_url.scheme,
                    parsed_url.netloc,
                    parsed_url.path,
                    parsed_url.params,
                    new_query,
                    parsed_url.fragment
                ))

                # Ensure the URL is absolute by joining with the base URL
                full_url = urljoin(base_url, clean_url)
                image_urls.add(full_url)

    return list(image_urls)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def download_image(url, output_dir, headers, logger=None):
    """
    Downloads an image from the specified URL to the output directory.
    Retries up to 3 times with a 2-second wait between attempts on failure.

    Args:
        url (str): The image URL to download.
        output_dir (str): The directory to save the downloaded image.
        headers (dict): HTTP headers to include in the request.
        logger (logging.Logger, optional): Logger object for logging. Defaults to None.

    Raises:
        Exception: If the download fails after retries.
    """
    try:
        # Extract the image filename from the URL path
        filename = os.path.basename(urlparse(url).path)
        local_filename = os.path.join(output_dir, filename)

        # Check if the file already exists to avoid redundant downloads
        if os.path.exists(local_filename):
            if logger:
                logger.info(f"Already exists: {local_filename}")
            else:
                print(f"Already exists: {local_filename}")
            return

        # Stream the download to handle large files efficiently
        with requests.get(url, stream=True, headers=headers) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
        # Log or print the successful download
        if logger:
            logger.info(f"Downloaded: {local_filename}")
        else:
            print(f"Downloaded: {local_filename}")
    except requests.RequestException as e:
        # Log or print the error before retrying
        if logger:
            logger.error(f"Failed to download {url}: {e}")
        else:
            print(f"Failed to download {url}: {e}")
        raise
    except Exception as e:
        # Catch all other exceptions (e.g., OSError from open)
        if logger:
            logger.error(f"Error downloading {url}: {e}")
        else:
            print(f"Error downloading {url}: {e}")
        raise  # Trigger retry

def setup_logging():
    """
    Sets up logging to a file 'image_downloader.log'.

    Returns:
        logging.Logger: Configured logger object.
    """
    logging.basicConfig(
        filename='image_downloader.log',
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    return logging.getLogger('ImageDownloader')

def main():
    """
    Main function to orchestrate the downloading of images based on provided arguments.
    """
    # Parse command-line arguments
    args = parse_arguments()
    order_id = args.order_id
    extensions = args.extensions
    output_dir = args.output
    base_url = args.base_url
    user_remove_params = args.remove_params
    raw_image = args.raw_image
    no_watermark = args.no_watermark
    enable_parallel = args.parallel
    enable_logging = args.log

    # Setup logging if enabled
    logger = None
    if enable_logging:
        logger = setup_logging()
        logger.info(f"Starting download for order ID: {order_id}")

    # Construct the full page URL
    page_url = get_page_url(base_url, order_id)
    
    # Extract base URL for constructing full image URLs
    parsed_page_url = urlparse(page_url)
    base_url = f"{parsed_page_url.scheme}://{parsed_page_url.netloc}"

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Define headers to mimic a real browser (optional but recommended)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " 
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/117.0.0.0 Safari/537.36"
    }

    print(f"Fetching HTML content from: {page_url}")
    if enable_logging:
        logger.info(f"Fetching HTML content from: {page_url}")
    html_content = get_html_content(page_url, headers)
    if not html_content:
        print("No HTML content to process.")
        if enable_logging:
            logger.warning("No HTML content fetched.")
        sys.exit(1)

    if enable_logging:
        logger.info("HTML content fetched successfully.")

    print("Extracting image URLs...")
    if enable_logging:
        logger.info("Extracting image URLs.")

    # Prepare parameters to remove based on flags
    remove_params = {}
    if raw_image:
        remove_params['raw_image'] = True
    if no_watermark:
        remove_params['no_watermark'] = True
    if user_remove_params:
        remove_params['additional_params'] = user_remove_params
    else:
        remove_params['additional_params'] = []

    # Extract image URLs with the specified criteria
    image_urls = extract_image_urls(html_content, base_url, extensions, remove_params)
    print(f"Found {len(image_urls)} unique image URLs.")
    if enable_logging:
        logger.info(f"Found {len(image_urls)} image URLs.")

    if not image_urls:
        print("No images found. Please ensure that the page is accessible and contains image links.")
        if enable_logging:
            logger.warning("No images found to download.")
        sys.exit(1)

    print("Starting image downloads...")

    if enable_parallel:
        # Enable parallel downloads using ThreadPoolExecutor
        print("Downloading images in parallel using multithreading...")
        if enable_logging:
            logger.info("Starting parallel downloads.")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit download tasks for each image URL
            futures = [
                executor.submit(download_image, url, output_dir, headers, logger)
                for url in image_urls
            ]
            # Display a progress bar while downloads are in progress
            for _ in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Downloading"):
                pass
    else:
        # Sequential downloads with a progress bar
        for url in tqdm(image_urls, desc="Downloading images"):
            download_image(url, output_dir, headers, logger)

    print("All downloads completed.")
    if enable_logging:
        logger.info("All downloads completed.")

if __name__ == "__main__":
    main()
