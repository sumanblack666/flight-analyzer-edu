# flight-analyzer-edu

> 🎓 An educational Python project demonstrating GUI development, data analysis, and API interactions through a flight price analysis tool, with a focus on AirAsia flights. For learning purposes only.

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Educational](https://img.shields.io/badge/purpose-educational-green.svg)](README.md#educational-context)

⚠️ **DISCLAIMER: EDUCATIONAL PURPOSE ONLY**

This project is created strictly for **EDUCATIONAL PURPOSES** only. Web scraping may be against the terms of service of many websites and could be illegal in certain contexts. This code is meant to demonstrate programming concepts and should not be used for actual data collection from any website without proper authorization.

The creators and contributors of this project:
- Do not endorse unauthorized scraping of any website
- Are not responsible for any misuse of this code
- Recommend always checking and complying with a website's terms of service and robots.txt
- Suggest obtaining proper authorization before collecting any data from websites

## About

A Python desktop application showcasing:
- GUI development with tkinter
- Data analysis with pandas
- API interaction patterns
- Thread management
- File I/O operations
- Error handling
- Event-driven programming

## Features

- 🔍 Search multiple destinations simultaneously
- 🔄 Support for both one-way and round-trip flights
- 📅 Weekend flight indicators
- 📊 Comprehensive price analysis
- 💾 Excel export of raw data and analysis
- 🎯 Customizable search parameters
- 🔍 Flexible sorting options

## Requirements

- Python 3.8 or higher
- Required Python packages (install via `pip install -r requirements.txt`):
  - pandas
  - requests

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/flight-analyzer-edu.git
   cd flight-analyzer-edu
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/MacOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python airasiav2.py
   ```

2. Enter your AirAsia API access token
3. Configure search parameters:
   - Select departure airport
   - Choose destination airports (multiple selection supported)
   - Set date range
   - Choose flight type (one-way/round-trip)
   - Set trip duration for round-trips
4. Click "Fetch Flight Data" to start the search
5. Results will be automatically exported to Excel

## Creating an Executable

You can create a standalone executable using PyInstaller:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Create the executable:
   ```bash
   # Windows
   pyinstaller --onefile --windowed --icon=app_icon.ico airasiav2.py
   
   # Linux/MacOS
   pyinstaller --onefile --windowed airasiav2.py
   ```

The executable will be created in the `dist` directory.

### Executable Compilation Notes

- The `--onefile` flag creates a single executable file
- The `--windowed` flag prevents a console window from appearing
- Add `--icon=path_to_icon.ico` to set a custom icon (Windows)
- The compiled executable can be found in the `dist` directory
- First run may take longer due to unpacking

## City Codes Management

- The application maintains a `City_Codes_List.txt` file for airport codes
- Default codes are provided if the file doesn't exist
- Add/remove codes through the GUI interface
- Changes are automatically saved

## Analysis Features

- Sort results by:
  - Price (Low to High/High to Low)
  - Trip duration
  - Destination
- Weekend flight indicators for better planning
- Customizable trip duration range
- Excel export with separate sheets for each route

## Troubleshooting

1. **API Token Issues**
   - Ensure your AirAsia API token is valid and not expired
   - Check for proper token formatting

2. **Rate Limiting**
   - Adjust the delay between requests if encountering 417 errors
   - Default delay is 2.5 seconds

3. **Excel Export Issues**
   - Ensure Excel is not open while exporting
   - Check write permissions in the directory

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Legal Notice

This software is provided for educational purposes only. Any use of this code for scraping websites without proper authorization may violate:
- Website terms of service
- Applicable laws and regulations
- API usage agreements

Users are solely responsible for ensuring their use of this software complies with all applicable terms, conditions, and laws.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Educational Context

This project serves as a learning resource for:
- Python programming concepts
- GUI development with tkinter
- Data analysis with pandas
- API interaction patterns
- Software architecture principles

Remember: Always obtain proper authorization before collecting data from any website or API.
