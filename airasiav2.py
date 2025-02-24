import requests
import pandas as pd
import datetime
from time import sleep
import tkinter as tk
from tkinter import messagebox, ttk
import os
import threading
import math

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(self.tooltip, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class FlightPriceScraper:
    def __init__(self):
        # In-memory storage for flight data and analysis results
        self.flight_data = []
        self.analysis_data = None
        self.city_codes_file = 'City_Codes_List.txt'
        # Load city codes from file (or fallback)
        self.city_codes = self.load_city_codes()
        # Setup the GUI
        self.root = tk.Tk()
        self.root.title("Flight Price Scraper and Analyzer")
        # Set up window close protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.setup_gui()

    def save_city_codes(self):
        """Save current city codes to file."""
        try:
            departure_codes = list(self.departure_listbox.get(0, tk.END))
            with open(self.city_codes_file, 'w', encoding='utf-8') as file:
                for code in departure_codes:
                    file.write(f"{code}\n")
            return True
        except Exception as e:
            self.log_message(f"Error saving city codes: {e}")
            return False

    def on_closing(self):
        """Handle window closing event."""
        self.save_city_codes()
        self.root.destroy()

    def load_city_codes(self, file_path='City_Codes_List.txt'):
        """Load city codes from file or use fallback list."""
        codes = []
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    if line.strip():
                        # Expected format: CODE - City
                        codes.append(line.strip())
        else:
            codes = [
                "KUL - Kuala Lumpur", "KBV - Kota Bharu",
                "LGK - Langkawi", "KUA - Kuantan", "PEN - Penang"
            ]
        return codes

    def log_message(self, message):
        """Append a log message with timestamp."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def fetch_flight_data(self):
        """Fetch flight data based on user inputs and then run analysis."""
        access_token = self.token_entry.get().strip()
        if not access_token:
            messagebox.showerror("Input Error", "Please enter access token.")
            return

        try:
            delay_seconds = float(self.delay_entry.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Invalid delay input. Please enter a number.")
            return

        # Get selected departure code (only one selection allowed)
        dep_selection = self.departure_listbox.curselection()
        if not dep_selection:
            messagebox.showerror("Input Error", "Please select a departure code.")
            return
        dep_item = self.departure_listbox.get(dep_selection[0])
        depart_code = dep_item.split(" - ")[0]

        # Get selected destination codes (multiple selection allowed)
        dest_indices = self.destination_listbox.curselection()
        if not dest_indices:
            messagebox.showerror("Input Error", "Please select at least one destination code.")
            return
        destination_codes = [self.destination_listbox.get(i).split(" - ")[0] for i in dest_indices]

        # Get flight type (One Way or Round Trip)
        flight_type = self.flight_type.get()

        # Get date range from user inputs
        from_date_str = self.from_date_entry.get().strip()
        to_date_str = self.to_date_entry.get().strip()
        try:
            start_date = datetime.datetime.strptime(from_date_str, "%d/%m/%Y").date()
            end_date = datetime.datetime.strptime(to_date_str, "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Input Error", "Invalid date format. Please use dd/mm/yyyy.")
            return
        if start_date > end_date:
            messagebox.showerror("Input Error", "From Date must be earlier than To Date.")
            return

        # Clear previous flight data, analysis, and logs
        self.flight_data = []
        self.analysis_data = None
        self.log_text.delete("1.0", tk.END)
        self.log_message("Starting flight data fetch...")

        # Use a 30-day window for each API call
        range_days = 30
        num_iterations = math.ceil((end_date - start_date).days / range_days) + 1
        # Calculate total requests (×2 for round-trip, 1 for one-way)
        reqs_per_dest = 2 if flight_type == "Round Trip" else 1
        total_requests = len(destination_codes) * num_iterations * reqs_per_dest
        self.progress_bar['maximum'] = total_requests
        self.progress_bar['value'] = 0

        headers = {
            'accept': '*/*',
            'authorization': f'Bearer {access_token}',
            'channel_hash': 'c5e9028b4295dcf4d7c239af8231823b520c3cc15b99ab04cde71d0ab18d65bc',
            'origin': 'https://www.airasia.com',
            'referer': 'https://www.airasia.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36',
            'user-type': 'anonymous'
        }
        base_url = "https://flights.airasia.com/fp/lfc/v1/lowfare"
        currency = "MYR"

        # Loop over each destination and over each date window
        for destination in destination_codes:
            current_date = start_date
            while current_date <= end_date:
                formatted_date = current_date.strftime("%d/%m/%Y")
                params = {
                    'departStation': depart_code,
                    'arrivalStation': destination,
                    'currency': currency,
                    'airlineProfile': 'all',
                    'date': formatted_date,
                    'range': range_days,
                    'isDestinationCity': 'false',
                    'isOriginCity': 'false'
                }
                # Fetch outbound flights
                self.log_message(f"Fetching outbound: {depart_code} -> {destination} on {formatted_date}")
                try:
                    response = requests.get(base_url, headers=headers, params=params)
                    if response.status_code == 417:
                        self.log_message(f"Skipping window starting {formatted_date} (417 error).")
                        current_date += datetime.timedelta(days=range_days)
                        continue
                    response.raise_for_status()
                    data = response.json().get('data', [])
                    for flight in data:
                        self.flight_data.append({
                            'departure_station': depart_code,
                            'arrival_station': destination,
                            'departure_date': flight['departureDate'],
                            'price': flight['price'],
                            'formatted_price': flight.get('shortFormattedPrice', ''),
                            'short_price': flight.get('shortPrice', ''),
                            'airline_profile': flight['airlineProfile'],
                            'aa_flight': flight['aaFlight'],
                            'direction': 'outbound',
                            'fetch_date': datetime.date.today().strftime("%Y-%m-%d")
                        })
                    self.progress_bar['value'] += 1
                    self.progress_label.config(
                        text=f"Fetched outbound {depart_code}->{destination} for {formatted_date}"
                    )
                    self.root.update_idletasks()
                except requests.exceptions.RequestException as e:
                    self.log_message(f"Error (outbound) on {formatted_date}: {e}")
                # Sleep after the outbound request
                sleep(delay_seconds)

                # For Round Trip, fetch return flights
                if flight_type == "Round Trip":
                    params_return = {
                        'departStation': destination,
                        'arrivalStation': depart_code,
                        'currency': currency,
                        'airlineProfile': 'all',
                        'date': formatted_date,
                        'range': range_days,
                        'isDestinationCity': 'false',
                        'isOriginCity': 'false'
                    }
                    self.log_message(f"Fetching return: {destination} -> {depart_code} on {formatted_date}")
                    try:
                        response = requests.get(base_url, headers=headers, params=params_return)
                        if response.status_code == 417:
                            self.log_message(f"Skipping return window starting {formatted_date} (417 error).")
                            current_date += datetime.timedelta(days=range_days)
                            continue
                        response.raise_for_status()
                        data = response.json().get('data', [])
                        for flight in data:
                            self.flight_data.append({
                                'departure_station': destination,
                                'arrival_station': depart_code,
                                'departure_date': flight['departureDate'],
                                'price': flight['price'],
                                'formatted_price': flight.get('shortFormattedPrice', ''),
                                'short_price': flight.get('shortPrice', ''),
                                'airline_profile': flight['airlineProfile'],
                                'aa_flight': flight['aaFlight'],
                                'direction': 'return',
                                'fetch_date': datetime.date.today().strftime("%Y-%m-%d")
                            })
                        self.progress_bar['value'] += 1
                        self.progress_label.config(
                            text=f"Fetched return {destination}->{depart_code} for {formatted_date}"
                        )
                        self.root.update_idletasks()
                    except requests.exceptions.RequestException as e:
                        self.log_message(f"Error (return) on {formatted_date}: {e}")
                    # Sleep after the return request
                    sleep(delay_seconds)

                current_date += datetime.timedelta(days=range_days)

        # After scraping, if Round Trip, run analysis
        if flight_type == "Round Trip":
            self.perform_analysis()

        # Export both flight data and (if available) analysis to Excel
        self.export_to_excel()
        messagebox.showinfo("Success", "Flight data fetched, analyzed, and exported to Excel.")
        self.log_message("Flight data fetching and analysis complete.")

    def perform_analysis(self):
        """Perform analysis for cheap round-trip tickets using user-specified trip day range."""
        if not self.flight_data:
            self.log_message("No flight data available for analysis.")
            return None

        # Retrieve minimum and maximum trip days from user input
        try:
            min_trip_days = int(self.min_trip_days_entry.get().strip())
            max_trip_days = int(self.max_trip_days_entry.get().strip())
        except ValueError:
            self.log_message("Invalid trip days input; using defaults 3 and 5.")
            min_trip_days = 3
            max_trip_days = 5

        # Get sort preference
        sort_by = self.sort_by.get()

        df = pd.DataFrame(self.flight_data)
        try:
            df['departure_date'] = pd.to_datetime(df['departure_date'], format="%d/%m/%Y", errors='coerce')
        except Exception as e:
            self.log_message(f"Error converting dates: {e}")
            return None

        outbound = df[df['direction'] == 'outbound']
        inbound = df[df['direction'] == 'return']
        results = []
        for idx, out_row in outbound.iterrows():
            out_date = out_row['departure_date']
            start_return = out_date + pd.Timedelta(days=min_trip_days)
            end_return = out_date + pd.Timedelta(days=max_trip_days)
            matching_inbounds = inbound[
                (inbound['departure_station'] == out_row['arrival_station']) &
                (inbound['arrival_station'] == out_row['departure_station']) &
                (inbound['departure_date'] >= start_return) &
                (inbound['departure_date'] <= end_return)
            ]
            for jdx, in_row in matching_inbounds.iterrows():
                total_price = out_row['price'] + in_row['price']
                # Calculate the number of trip days
                trip_days = (in_row['departure_date'] - out_date).days
                # Check if dates are weekends
                is_outbound_weekend = out_date.weekday() >= 5
                is_inbound_weekend = in_row['departure_date'].weekday() >= 5
                
                results.append({
                    'Destination': out_row['arrival_station'],
                    'Outbound Date': out_date.strftime("%d/%m/%Y"),
                    'Outbound Weekend': '🏖️' if is_outbound_weekend else '',
                    'Inbound Date': in_row['departure_date'].strftime("%d/%m/%Y"),
                    'Inbound Weekend': '🏖️' if is_inbound_weekend else '',
                    'Outbound Price': out_row['price'],
                    'Inbound Price': in_row['price'],
                    'Total Price': total_price,
                    'Trip Days': trip_days
                })
        if results:
            analysis_df = pd.DataFrame(results)
            
            # Apply sorting based on user selection
            if self.sort_by.get() == 'Price (Low to High)':
                analysis_df = analysis_df.sort_values(by='Total Price')
            elif self.sort_by.get() == 'Price (High to Low)':
                analysis_df = analysis_df.sort_values(by='Total Price', ascending=False)
            elif self.sort_by.get() == 'Trip Days':
                analysis_df = analysis_df.sort_values(by=['Trip Days', 'Total Price'])
            elif self.sort_by.get() == 'Destination':
                analysis_df = analysis_df.sort_values(by=['Destination', 'Total Price'])
            self.analysis_data = analysis_df
            self.log_message("Analysis complete.")
            return analysis_df
        else:
            self.log_message("No valid round-trip combinations found for analysis.")
            return None

    def export_to_excel(self):
        """Export flight data (grouped by route) and analysis (if available) to an Excel file without overwriting."""
        if not self.flight_data:
            messagebox.showwarning("No Data", "No flight data available to export.")
            return
        df = pd.DataFrame(self.flight_data)
        base_filename = f"Flight_Prices_{datetime.date.today().strftime('%Y%m%d')}.xlsx"
        excel_filename = base_filename
        counter = 1
        # If file exists, append a counter until an unused filename is found.
        while os.path.exists(excel_filename):
            excel_filename = f"Flight_Prices_{datetime.date.today().strftime('%Y%m%d')}_{counter}.xlsx"
            counter += 1
        with pd.ExcelWriter(excel_filename) as writer:
            # Export raw flight data grouped by route (departure to arrival)
            for (dep, arr), group in df.groupby(['departure_station', 'arrival_station']):
                sheet_name = f"{dep}_to_{arr}"[:31]  # Sheet names max 31 chars
                group.to_excel(writer, sheet_name=sheet_name, index=False)
            # Export analysis data if available
            if self.analysis_data is not None and not self.analysis_data.empty:
                self.analysis_data.to_excel(writer, sheet_name="Analysis", index=False)
        self.log_message(f"Data exported to {excel_filename}")

    def start_fetch_thread(self):
        """Start flight data fetch in a background thread."""
        threading.Thread(target=self.fetch_flight_data, daemon=True).start()

    # --- Functions for Editing Departure Codes ---
    def add_departure_code(self):
        code = self.departure_entry.get().strip()
        if code:
            self.departure_listbox.insert(tk.END, code)
            self.departure_entry.delete(0, tk.END)
            self.destination_listbox.insert(tk.END, code)  # Add to both lists
            self.save_city_codes()
        else:
            messagebox.showerror("Input Error", "Enter a departure code to add.")

    def delete_departure_code(self):
        selected = self.departure_listbox.curselection()
        if not selected:
            messagebox.showerror("Selection Error", "Select a departure code to delete.")
            return
        # Delete only from departure list
        for index in reversed(selected):
            self.departure_listbox.delete(index)
        self.save_city_codes()

    # --- Functions for Editing Destination Codes ---
    def add_destination_code(self):
        code = self.destination_entry.get().strip()
        if code:
            self.destination_listbox.insert(tk.END, code)
            self.destination_entry.delete(0, tk.END)
            self.departure_listbox.insert(tk.END, code)  # Add to both lists
            self.save_city_codes()
        else:
            messagebox.showerror("Input Error", "Enter a destination code to add.")

    def delete_destination_code(self):
        selected = self.destination_listbox.curselection()
        if not selected:
            messagebox.showerror("Selection Error", "Select a destination code to delete.")
            return
        # Delete only from destination list
        for index in reversed(selected):
            self.destination_listbox.delete(index)
        self.save_city_codes()

    def setup_gui(self):
        """Set up the GUI components with enhanced styling."""
        # Configure root window
        self.root.configure(bg='#f0f0f0')
        self.root.title("AirAsia Flight Price Analyzer")
        
        # Configure ttk styles
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 9))
        style.configure('TButton', font=('Arial', 9))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        main_frame.grid(row=0, column=0, sticky="NSEW")
        
        # Configure grid weight
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Authentication Frame
        auth_frame = ttk.LabelFrame(main_frame, text="Authentication & Settings", padding="5")
        auth_frame.grid(row=0, column=0, columnspan=4, sticky="NSEW", padx=5, pady=5)
        
        # Access Token with improved layout
        token_frame = ttk.Frame(auth_frame)
        token_frame.grid(row=0, column=0, sticky="W", padx=5, pady=5)
        ttk.Label(token_frame, text="Access Token:", style='Header.TLabel').grid(row=0, column=0, sticky="W", padx=5)
        self.token_entry = ttk.Entry(token_frame, show="*", width=40)
        self.token_entry.grid(row=0, column=1, sticky="W", padx=5)
        ToolTip(self.token_entry, "Enter your AirAsia API access token")

        # Request Delay with improved layout
        delay_frame = ttk.Frame(auth_frame)
        delay_frame.grid(row=1, column=0, sticky="W", padx=5, pady=5)
        ttk.Label(delay_frame, text="Request Delay:", style='Header.TLabel').grid(row=0, column=0, sticky="W", padx=5)
        self.delay_entry = ttk.Entry(delay_frame, width=10)
        self.delay_entry.insert(0, "2.5")
        self.delay_entry.grid(row=0, column=1, sticky="W", padx=5)
        ttk.Label(delay_frame, text="seconds").grid(row=0, column=2, sticky="W", padx=2)
        ToolTip(self.delay_entry, "Time to wait between API requests (in seconds)")

        # Cities Selection Frame
        cities_frame = ttk.LabelFrame(main_frame, text="Airport Selection", padding="5")
        cities_frame.grid(row=2, column=0, columnspan=4, sticky="NSEW", padx=5, pady=10)

        # Departure Code Section
        dep_section = ttk.Frame(cities_frame)
        dep_section.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
        ttk.Label(dep_section, text="Departure Airport:", style='Header.TLabel').grid(row=0, column=0, sticky="W", padx=5)
        
        dep_frame = ttk.Frame(dep_section)
        dep_frame.grid(row=1, column=0, sticky="W", padx=5, pady=2)
        
        # Enhanced Listbox with better styling
        dep_scroll = ttk.Scrollbar(dep_frame, orient=tk.VERTICAL)
        self.departure_listbox = tk.Listbox(dep_frame, height=5, width=25,
                                          exportselection=0,
                                          yscrollcommand=dep_scroll.set,
                                          selectmode=tk.SINGLE,
                                          font=('Arial', 9),
                                          background='white',
                                          selectbackground='#0078D7')
        dep_scroll.config(command=self.departure_listbox.yview)
        self.departure_listbox.grid(row=0, column=0, rowspan=2, sticky="NSEW")
        dep_scroll.grid(row=0, column=1, rowspan=2, sticky="NS")
        
        # Control frame for entry and buttons
        dep_control = ttk.Frame(dep_frame)
        dep_control.grid(row=0, column=2, padx=5)
        
        self.departure_entry = ttk.Entry(dep_control, width=20)
        self.departure_entry.grid(row=0, column=0, padx=2, pady=2)
        ToolTip(self.departure_entry, "Enter airport code and city (e.g., KUL - Kuala Lumpur)")
        
        btn_frame = ttk.Frame(dep_control)
        btn_frame.grid(row=1, column=0, pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_departure_code).grid(row=0, column=0, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_departure_code).grid(row=0, column=1, padx=2)
        
        # Pre-populate departure codes
        for code in self.city_codes:
            self.departure_listbox.insert(tk.END, code)

        # Destination Section
        dest_section = ttk.Frame(cities_frame)
        dest_section.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)
        ttk.Label(dest_section, text="Destination Airports:", style='Header.TLabel').grid(row=0, column=0, sticky="W", padx=5)
        
        dest_frame = ttk.Frame(dest_section)
        dest_frame.grid(row=1, column=0, sticky="W", padx=5, pady=2)
        
        # Enhanced Listbox with better styling
        dest_scroll = ttk.Scrollbar(dest_frame, orient=tk.VERTICAL)
        self.destination_listbox = tk.Listbox(dest_frame,
                                            selectmode=tk.MULTIPLE,
                                            height=5,
                                            width=25,
                                            exportselection=0,
                                            yscrollcommand=dest_scroll.set,
                                            font=('Arial', 9),
                                            background='white',
                                            selectbackground='#0078D7')
        dest_scroll.config(command=self.destination_listbox.yview)
        self.destination_listbox.grid(row=0, column=0, rowspan=2, sticky="NSEW")
        dest_scroll.grid(row=0, column=1, rowspan=2, sticky="NS")
        
        # Control frame for entry and buttons
        dest_control = ttk.Frame(dest_frame)
        dest_control.grid(row=0, column=2, padx=5)
        
        self.destination_entry = ttk.Entry(dest_control, width=20)
        self.destination_entry.grid(row=0, column=0, padx=2, pady=2)
        ToolTip(self.destination_entry, "Enter airport code and city (e.g., KUL - Kuala Lumpur)")
        
        btn_frame = ttk.Frame(dest_control)
        btn_frame.grid(row=1, column=0, pady=5)
        ttk.Button(btn_frame, text="Add", command=self.add_destination_code).grid(row=0, column=0, padx=2)
        ttk.Button(btn_frame, text="Delete", command=self.delete_destination_code).grid(row=0, column=1, padx=2)
        
        # Help text for multiple selection
        ttk.Label(dest_section, text="Hold Ctrl to select multiple destinations",
                 font=('Arial', 8, 'italic')).grid(row=2, column=0, sticky="W", padx=5, pady=2)
        
        # Pre-populate destination codes
        for code in self.city_codes:
            self.destination_listbox.insert(tk.END, code)

        # Date Range Frame
        dates_frame = ttk.LabelFrame(main_frame, text="Travel Period", padding="5")
        dates_frame.grid(row=4, column=0, columnspan=4, sticky="NSEW", padx=5, pady=10)
        
        # From Date
        from_frame = ttk.Frame(dates_frame)
        from_frame.grid(row=0, column=0, sticky="W", padx=5, pady=5)
        ttk.Label(from_frame, text="From Date:", style='Header.TLabel').grid(row=0, column=0, sticky="W", padx=5)
        self.from_date_entry = ttk.Entry(from_frame, width=15)
        self.from_date_entry.insert(0, datetime.date.today().strftime("%d/%m/%Y"))
        self.from_date_entry.grid(row=0, column=1, padx=5)
        ToolTip(self.from_date_entry, "Enter start date in dd/mm/yyyy format")
        
        # To Date
        to_frame = ttk.Frame(dates_frame)
        to_frame.grid(row=1, column=0, sticky="W", padx=5, pady=5)
        ttk.Label(to_frame, text="To Date:", style='Header.TLabel').grid(row=0, column=0, sticky="W", padx=5)
        default_to_date = (datetime.date.today() + datetime.timedelta(days=365)).strftime("%d/%m/%Y")
        self.to_date_entry = ttk.Entry(to_frame, width=15)
        self.to_date_entry.insert(0, default_to_date)
        self.to_date_entry.grid(row=0, column=1, padx=5)
        ToolTip(self.to_date_entry, "Enter end date in dd/mm/yyyy format")
        
        # Format hint
        ttk.Label(dates_frame, text="Format: dd/mm/yyyy",
                 font=('Arial', 8, 'italic')).grid(row=2, column=0, sticky="W", padx=5, pady=2)

        # Flight Type Frame
        flight_frame = ttk.LabelFrame(main_frame, text="Flight Type", padding="5")
        flight_frame.grid(row=6, column=0, columnspan=4, sticky="NSEW", padx=5, pady=10)
        
        # Radio buttons in a dedicated frame with better layout
        radio_frame = ttk.Frame(flight_frame)
        radio_frame.grid(row=0, column=0, sticky="W", padx=5, pady=5)
        
        self.flight_type = tk.StringVar(value="Round Trip")
        
        one_way_radio = ttk.Radiobutton(radio_frame,
                                       text="One Way",
                                       variable=self.flight_type,
                                       value="One Way")
        one_way_radio.grid(row=0, column=0, padx=15, pady=2)
        ToolTip(one_way_radio, "Search for one-way flights only")
        
        round_trip_radio = ttk.Radiobutton(radio_frame,
                                          text="Round Trip",
                                          variable=self.flight_type,
                                          value="Round Trip")
        round_trip_radio.grid(row=0, column=1, padx=15, pady=2)
        ToolTip(round_trip_radio, "Search for return flights with price analysis")

        # Analysis Options Section
        analysis_frame = ttk.LabelFrame(main_frame, text="Analysis Options", padding="5")
        analysis_frame.grid(row=7, column=0, columnspan=4, sticky="NSEW", padx=5, pady=10)
        
        # Trip Days Input with improved layout
        trip_frame = ttk.Frame(analysis_frame)
        trip_frame.grid(row=0, column=0, columnspan=2, sticky="W", padx=5, pady=5)
        
        ttk.Label(trip_frame, text="Trip Duration:", style='Header.TLabel').grid(row=0, column=0, sticky="W", padx=5)
        
        # Min Days
        min_frame = ttk.Frame(trip_frame)
        min_frame.grid(row=0, column=1, padx=10)
        ttk.Label(min_frame, text="Min:").grid(row=0, column=0)
        self.min_trip_days_entry = ttk.Entry(min_frame, width=5)
        self.min_trip_days_entry.insert(0, "3")
        self.min_trip_days_entry.grid(row=0, column=1, padx=2)
        ToolTip(self.min_trip_days_entry, "Minimum number of days for the trip")
        
        # Max Days
        max_frame = ttk.Frame(trip_frame)
        max_frame.grid(row=0, column=2, padx=10)
        ttk.Label(max_frame, text="Max:").grid(row=0, column=0)
        self.max_trip_days_entry = ttk.Entry(max_frame, width=5)
        self.max_trip_days_entry.insert(0, "5")
        self.max_trip_days_entry.grid(row=0, column=1, padx=2)
        ToolTip(self.max_trip_days_entry, "Maximum number of days for the trip")
        
        # Sorting Options
        sort_frame = ttk.Frame(analysis_frame)
        sort_frame.grid(row=1, column=0, columnspan=2, sticky="W", padx=5, pady=5)
        
        ttk.Label(sort_frame, text="Sort Results By:", style='Header.TLabel').grid(row=0, column=0, sticky="W", padx=5)
        self.sort_by = tk.StringVar(value="Price (Low to High)")
        sort_options = ttk.Combobox(sort_frame, textvariable=self.sort_by, state="readonly", width=20)
        sort_options['values'] = ('Price (Low to High)', 'Price (High to Low)', 'Trip Days', 'Destination')
        sort_options.grid(row=0, column=1, padx=10)
        ToolTip(sort_options, "Choose how to sort the analysis results")
        
        # Weekend Legend
        legend_frame = ttk.Frame(analysis_frame)
        legend_frame.grid(row=2, column=0, columnspan=2, sticky="W", padx=5, pady=5)
        ttk.Label(legend_frame, text="Legend:", style='Header.TLabel').grid(row=0, column=0, sticky="W", padx=5)
        ttk.Label(legend_frame, text="🏖️ = Weekend Flight").grid(row=0, column=1, sticky="W", padx=5)

        # Operation Status Frame
        status_frame = ttk.LabelFrame(main_frame, text="Operation Status", padding="5")
        status_frame.grid(row=8, column=0, columnspan=4, sticky="NSEW", padx=5, pady=10)
        
        # Progress Section
        progress_section = ttk.Frame(status_frame)
        progress_section.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
        
        # Status label with improved styling
        self.progress_label = ttk.Label(progress_section,
                                      text="Ready to fetch flight data",
                                      style='Status.TLabel')
        self.progress_label.grid(row=0, column=0, columnspan=2, sticky="W", padx=5, pady=2)
        
        # Enhanced progress bar
        style = ttk.Style()
        style.configure('Accent.Horizontal.TProgressbar',
                       background='#0078D7',
                       troughcolor='#F0F0F0',
                       thickness=10)
        
        self.progress_bar = ttk.Progressbar(progress_section,
                                          orient="horizontal",
                                          length=350,
                                          mode="determinate",
                                          style='Accent.Horizontal.TProgressbar')
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="EW", padx=5, pady=5)
        
        # Action button with improved styling
        style.configure('Action.TButton',
                       font=('Arial', 10, 'bold'),
                       padding=5)
        
        fetch_button = ttk.Button(progress_section,
                                text="Fetch Flight Data",
                                command=self.start_fetch_thread,
                                style='Action.TButton')
        fetch_button.grid(row=2, column=0, columnspan=2, pady=10)
        ToolTip(fetch_button, "Start fetching flight prices and analyzing data")
        
        # Log Section with improved styling
        log_frame = ttk.LabelFrame(status_frame, text="Operation Log", padding="5")
        log_frame.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)
        
        # Configure log text widget with better styling
        self.log_text = tk.Text(log_frame,
                               height=8,
                               width=60,
                               font=('Consolas', 9),
                               background='#FFFFFF',
                               wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)
        
        # Enhanced scrollbar
        log_scrollbar = ttk.Scrollbar(log_frame,
                                    orient=tk.VERTICAL,
                                    command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.grid(row=0, column=1, sticky='NS')
        
        # Configure status label style
        style.configure('Status.TLabel',
                       font=('Arial', 9),
                       padding=2)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    scraper = FlightPriceScraper()
    scraper.run()
