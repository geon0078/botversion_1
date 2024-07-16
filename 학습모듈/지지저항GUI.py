import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import hdbscan
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches
from datetime import datetime

def fetch_and_plot_data():
    global df, support_resistance_lines, confidence

    ticker_symbol = entry_ticker.get()
    start_date = entry_start_date.get()
    end_date = entry_end_date.get()

    # Attempt to fetch data from KOSPI first
    ticker_symbol_ks = ticker_symbol + ".KS"
    ticker_symbol_kq = ticker_symbol + ".KQ"

    try:
        print(f"Fetching data for {ticker_symbol_ks} from {start_date} to {end_date}")
        # Fetch historical data for KOSPI
        ticker = yf.Ticker(ticker_symbol_ks)
        df_minute = ticker.history(interval='1d', start=start_date, end=end_date, actions=True, auto_adjust=True)

        if df_minute.empty:
            print(f"No data found for {ticker_symbol_ks}. Trying {ticker_symbol_kq}")
            # Fetch historical data for KOSDAQ
            ticker = yf.Ticker(ticker_symbol_kq)
            df_minute = ticker.history(interval='1d', start=start_date, end=end_date, actions=True, auto_adjust=True)
            if df_minute.empty:
                raise ValueError("No data found for the given ticker symbol and date range in both KOSPI and KOSDAQ.")
        
        print("Data fetched successfully.")
        
        # Extract closing prices
        df = df_minute[['Close']]

        if df.empty:
            raise ValueError("No closing price data available.")
        
        print("Closing price data extracted.")

        # Data normalization
        scaler = MinMaxScaler()
        data_normalized = scaler.fit_transform(df['Close'].values.reshape(-1, 1))
        
        print("Data normalized.")

        # Clustering for support and resistance lines
        clusterer = hdbscan.HDBSCAN(min_cluster_size=5)
        cluster_labels = clusterer.fit_predict(data_normalized)
        
        print("Clustering completed.")

        # Find median of each cluster to determine support/resistance lines
        unique_labels = set(cluster_labels)
        support_resistance_lines_normalized = [np.median(data_normalized[cluster_labels == label])
                                               for label in unique_labels if label != -1]

        # Inverse transform to original scale
        support_resistance_lines = scaler.inverse_transform(np.array(support_resistance_lines_normalized).reshape(-1, 1)).flatten()
        
        print("Support and resistance lines calculated.")

        # Calculate confidence
        cluster_sizes = [np.sum(cluster_labels == label) for label in unique_labels if label != -1]
        confidence = [size / np.max(cluster_sizes) for size in cluster_sizes]
        
        print("Confidence calculated.")

        update_charts()
        
    except ValueError as e:
        messagebox.showerror("Error", str(e))
        print(f"ValueError: {str(e)}")
    except Exception as e:
        messagebox.showerror("Unexpected Error", str(e))
        print(f"Unexpected Error: {str(e)}")

def update_charts(*args):
    # Get the confidence threshold from the slider
    confidence_threshold = slider_threshold.get() / 100
    
    high_confidence_lines = [(line, conf) for line, conf in zip(support_resistance_lines, confidence) if conf >= confidence_threshold]
    
    # Plot the closing prices and support/resistance lines
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(df.index, df['Close'], label='Close Price')

    for line, conf in high_confidence_lines:
        ax.axhline(line, linestyle='--', linewidth=2, color=(1 - conf, 0, conf), alpha=0.7)
        ax.text(df.index[-1], line, f'{line:.2f}', verticalalignment='bottom', horizontalalignment='right', color='black', fontsize=10)

    # Add legend
    red_patch = mpatches.Patch(color='red', label='Low Confidence')
    blue_patch = mpatches.Patch(color='blue', label='High Confidence')
    ax.legend(handles=[red_patch, blue_patch])

    ax.set_title(f'{entry_ticker.get()} High Confidence Support and Resistance Lines')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')

    # Clear the previous plot
    for widget in frame_plot.winfo_children():
        widget.destroy()

    # Display the plot in the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=frame_plot)
    canvas.draw()
    canvas.get_tk_widget().pack()
    
    print("Plot displayed successfully.")

    # Update confidence bar chart
    update_confidence_bar_chart(confidence)

def update_confidence_bar_chart(confidence):
    # Clear the previous bar chart
    for widget in frame_confidence.winfo_children():
        widget.destroy()
    
    # Create a new figure for the bar chart
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(range(len(confidence)), confidence, color='blue')
    ax.set_title('Confidence Levels of Support and Resistance Lines')
    ax.set_xlabel('Line Index')
    ax.set_ylabel('Confidence')
    
    # Display the bar chart in the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=frame_confidence)
    canvas.draw()
    canvas.get_tk_widget().pack()

def set_end_date_to_today():
    today = datetime.today().strftime('%Y-%m-%d')
    entry_end_date.delete(0, tk.END)
    entry_end_date.insert(0, today)

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()

# Create the main window
root = tk.Tk()
root.title("Stock Support and Resistance Lines")

# Create and place the widgets
label_ticker = tk.Label(root, text="Ticker Symbol:")
label_ticker.pack()

entry_ticker = tk.Entry(root)
entry_ticker.pack()

label_start_date = tk.Label(root, text="Start Date (YYYY-MM-DD):")
label_start_date.pack()

entry_start_date = tk.Entry(root)
entry_start_date.pack()

label_end_date = tk.Label(root, text="End Date (YYYY-MM-DD):")
label_end_date.pack()

entry_end_date = tk.Entry(root)
entry_end_date.pack()

button_set_today = tk.Button(root, text="Set End Date to Today", command=set_end_date_to_today)
button_set_today.pack()

button_fetch = tk.Button(root, text="Fetch and Plot Data", command=fetch_and_plot_data)
button_fetch.pack()

label_slider = tk.Label(root, text="Confidence Threshold:")
label_slider.pack()

slider_threshold = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=update_charts)
slider_threshold.set(50)
slider_threshold.pack()

# Frame to hold the plot
frame_plot = tk.Frame(root)
frame_plot.pack(fill=tk.BOTH, expand=True)

# Frame to hold the confidence bar chart
frame_confidence = tk.Frame(root)
frame_confidence.pack(fill=tk.BOTH, expand=True)

# Set the protocol for the window close button
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the Tkinter event loop
root.mainloop()
