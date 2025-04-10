# Chart Generator

A web application for generating interactive charts from Excel data.

## Project Structure

The application follows a modular architecture to make code more maintainable and easier to extend.

### Backend (Python/Flask)

```
chartgenerator/
├── config/               # Configuration files
│   ├── __init__.py
│   └── config.py         # App configuration
├── routes/               # Route handlers
│   ├── __init__.py
│   ├── file_routes.py    # File upload and data handling routes
│   └── chart_routes.py   # Chart generation routes
├── static/               # Static assets
│   ├── css/
│   ├── img/
│   └── js/
│       ├── main.js       # Main application script
│       └── modules/      # JavaScript modules
│           ├── fileUpload.js     # File upload functionality
│           ├── dataProcessor.js  # Data processing
│           ├── chartGenerator.js # Chart generation
│           └── uiController.js   # UI management
├── templates/            # HTML templates
│   └── index.html        # Main application page
├── uploads/              # Uploaded files (created at runtime)
├── utils/                # Utility functions
│   ├── __init__.py
│   ├── helpers.py        # Common helper functions
│   └── chart_processor.py# Chart data processing functions
├── __init__.py
├── app.py               # Main application entry point
└── README.md            # This file
```

### Frontend (JavaScript)

The JavaScript code has been modularized into the following components:

- **main.js**: Entry point that initializes and connects all modules
- **fileUpload.js**: Handles file upload functionality
- **dataProcessor.js**: Processes Excel data
- **chartGenerator.js**: Generates and manages charts
- **uiController.js**: Manages UI updates and interactions

## Running the Application

1. Install dependencies:
   ```
   pip install flask pandas openpyxl numpy
   ```

2. Run the application:
   ```
   python -m chartgenerator.app
   ```

3. Access the application in your browser at:
   ```
   http://localhost:5000
   ```

## How It Works

1. Upload an Excel file
2. Select the sheet, columns, and data filters
3. Choose a chart type
4. Generate and customize your chart
5. Download the chart as an image or as HTML code 