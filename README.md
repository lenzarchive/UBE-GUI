# UnityBundleExtractor GUI

A web-based graphical user interface for the robust UnityBundleExtractor tool, designed for analyzing and extracting assets from Unity3D bundle files. This project provides an accessible, modern web interface for all the powerful features of the original script, including asynchronous processing, selective extraction, and detailed metadata analysis.

## Features

* **Modern Web Interface**: A clean and responsive user interface built with Flask, allowing you to use the extractor from any modern web browser.
* **Drag & Drop File Upload**: Easily upload your main Unity bundle files (`.bundle`, `.unity3d`, `.assets`) along with any optional resource files (`.resS`) through a simple drag-and-drop interface.
* **Asynchronous Task Processing**: Uploads are handled asynchronously. A task queue system manages analysis and extraction jobs, allowing you to monitor progress without locking up the interface.
* **Real-time Status and Progress**: Track the status of your task in real-time, from its position in the queue to the progress of analysis and extraction, all updated dynamically on the page.
* **Comprehensive Bundle Analysis**: View detailed metadata about the uploaded bundle, including Unity version, platform, compression type, and a complete list of all contained assets grouped by type.
* **Selective Asset Extraction**: Browse the full list of assets, filter them by name, and select specific items or entire categories for extraction. The selected assets are then conveniently packaged into a single `.ZIP` archive for download.
* **Structured Output**: Extracted assets within the ZIP file are organized into type-specific subdirectories (e.g., `Texture2D/`, `MonoBehaviour/`, `Mesh/`) for easy navigation.
* **Robust Backend**: The application is built with a scalable architecture, including a worker pool to process multiple tasks efficiently and a scheduler for automated cleanup of old files.
* **Easy Deployment with Docker**: Comes fully configured for containerization with a `Dockerfile` and `docker-compose.yml`, allowing for quick and consistent deployment in any environment.

## Disclaimer

This tool is provided for **educational and research purposes only**. It is intended to help developers, researchers, and enthusiasts understand the structure of Unity game assets and facilitate legitimate modding, analysis, or asset recovery for **personal projects where legal permissions are obtained**.

## Requirements

To run this application, you need Python 3.7+ and Docker (for containerized deployment). The following Python libraries are required:

* UnityPy>=1.10.0
* Flask>=2.3.0
* Werkzeug>=2.3.0
* lz4>=4.3.0
* Pillow>=9.5.0
* tqdm>=4.65.0

You can install these dependencies using pip:

```bash
pip install -r requirements.txt
```

## How to Use

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/lenzarchive/UnityBundleExtractor-Web.git
    cd UnityBundleExtractor-Web
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**:

    * **For development**:
        ```bash
        python app.py
        ```
        The application will be available at `http://127.0.0.1:5000`.

    * **For production (using Gunicorn)**:
        ```bash
        gunicorn --bind 0.0.0.0:5000 wsgi:application
        ```

    * **Using Docker (Recommended)**:
        Build and run the application using Docker Compose.
        ```bash
        docker-compose up --build
        ```
        The application will be available at `http://localhost:5000`.

4.  **Access the GUI**:
    Open your web browser and navigate to the appropriate URL.

5.  **Upload and Analyze**:
    Drag and drop your Unity bundle file into the upload area or use the file chooser. The analysis will start automatically.

6.  **Extract and Download**:
    Once the analysis is complete, select the assets you wish to extract and click the "Extract Selected as .ZIP" button. Your download will begin shortly.

## Contributing

Encountered a bug? Have an idea for a new feature? We welcome contributions! Please feel free to:

1.  **Open an Issue**: Describe the bug or suggest a new feature.
2.  **Submit a Pull Request**: Fork the repository, make your changes, and submit a pull request.

Your contributions help make this tool better for everyone!

## Donate

Saweria: [https://saweria.co](https://saweria.co/alwizba)

Ko-fi: [https://ko-fi.com](https://ko-fi.com/alwizba)

BTC: `bc1q0ay7shy6zyy3xduf9hgsgu5crfzvpes93d48a6`

## Credit

Thanks for using this script!
Credit: [@alwizba](https://github.com/lenzarchive)

## License

This script is licensed under the MIT License. See the `LICENSE` file for more details.
