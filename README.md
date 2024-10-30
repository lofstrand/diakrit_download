# 📄 **Image Downloader Script Documentation**

## 🚀 **Overview**

The **Image Downloader Script** is a versatile Python tool designed to download images from the Diakrit backend based on a specific `orderId`. It offers flexibility in selecting image file extensions, selectively removing query parameters, enabling parallel downloads for efficiency, and logging download activities for tracking and debugging.

## ⚠️ **Disclaimer**

**Important:**  
_The images may only be used for private use. The usage rights may not be transferred/licensed to others._

\*_Ensure that you have the necessary permissions and rights to download and use these images. Unauthorized use or distribution may violate legal agreements and terms of service._

## 🌟 **Features**

- **Specify Order ID Separately**: Easily provide the `orderId` without modifying the base URL.
- **Support Multiple File Extensions**: Download images with various extensions such as `.jpg` and `.png`.
- **Selective Query Parameter Removal**:
  - `--raw_image`: Remove both `width` and `height` query parameters.
  - `--no_watermark`: Remove the `watermark` query parameter.
  - `--remove_params`: Remove additional specified query parameters.
- **Parallel Downloads**: Utilize multithreading to accelerate the download process.
- **Logging**: Enable detailed logging to monitor and debug download activities.
- **Progress Bar**: Visualize download progress in real-time using `tqdm`.

## 🛠 **Installation**

1. **Ensure Python 3.x is Installed**

   Verify Python installation:

   ```bash
   python --version
   ```

   or

   ```bash
   python3 --version
   ```

   If Python is not installed, download it from the [official website](https://www.python.org/downloads/) and follow the installation instructions.

2. **Install Required Python Libraries**

   Open your terminal or command prompt and run:

   ```bash
   pip install requests beautifulsoup4 tqdm tenacity
   ```

   If you're using Python 3 and `pip` refers to Python 2, use:

   ```bash
   pip3 install requests beautifulsoup4 tqdm tenacity
   ```

## 📖 **Usage**

Run the script using the command line, providing the necessary arguments and options.

### **Syntax**

```bash
python download_images.py ORDER_ID [options]
```

### **Positional Arguments**

- `ORDER_ID`: The unique identifier for the order whose images you want to download.

### **Optional Arguments**

| **Flag**                 | **Description**                                                           | **Example**                     |
| ------------------------ | ------------------------------------------------------------------------- | ------------------------------- |
| `-e`, `--extensions`     | List of image file extensions to download.                                | `-e .jpg .png`                  |
| `-o`, `--output`         | Directory to save downloaded images.                                      | `-o my_images`                  |
| `-b`, `--base_url`       | Base URL of the Diakrit portal. Defaults to `https://portal.diakrit.com`. | `-b https://portal.diakrit.com` |
| `--raw_image`            | Remove both `width` and `height` query parameters from image URLs.        | `--raw_image`                   |
| `--no_watermark`         | Remove the `watermark` query parameter from image URLs.                   | `--no_watermark`                |
| `-rp`, `--remove_params` | Remove additional specified query parameters from image URLs.             | `--remove_params foo bar`       |
| `-p`, `--parallel`       | Enable parallel downloads using multithreading.                           | `-p`                            |
| `-l`, `--log`            | Enable logging to `image_downloader.log`.                                 | `-l`                            |

### **Examples**

1. **Download `.jpg` Images with All Query Parameters**

   ```bash
   python download_images.py 12345678
   ```

   - **Behavior**: Downloads all `.jpg` images associated with `orderId=12345678`, including all query parameters.
   - **Output Directory**: `downloaded_images`

2. **Download `.jpg` and `.png` Images, Removing `watermark` and `width`**

   ```bash
   python download_images.py 12345678 -e .jpg .png --raw_image --no_watermark
   ```

   - **Behavior**: Downloads both `.jpg` and `.png` images, removing `width`, `height`, and `watermark` from the URLs.
   - **Output Directory**: `downloaded_images`

3. **Download Images to a Custom Directory with Parallel Downloads and Logging**

   ```bash
   python download_images.py 12345678 -e .jpg .png --raw_image --no_watermark -o my_images -p -l
   ```

   - **Behavior**: Downloads images as specified, saves them to `my_images`, enables parallel downloading, and logs activities.
   - **Output Directory**: `my_images`
   - **Logging**: Enabled (`image_downloader.log`)

4. **Remove Additional Query Parameters**

   ```bash
   python download_images.py 12345678 -e .jpg .png --remove_params foo bar
   ```

   - **Behavior**: Downloads `.jpg` and `.png` images, removing `foo` and `bar` query parameters from the URLs.
   - **Output Directory**: `downloaded_images`
