import tkinter as tk
from tkinter import ttk
import ccxt
import pandas as pd
from datetime import datetime
import threading
import time
import os
import json

# Configuration Management
class ConfigManager:
    CONFIG_FILE = 'grid_trading_config.json'
    
    @classmethod
    def load_config(cls):
        """Load configuration from a JSON file"""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return {}
    
    @classmethod
    def save_config(cls, config):
        """Save configuration to a JSON file"""
        try:
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

class GridTradingBot:
    def __init__(self):
        # Initialize the root window first
        self.root = tk.Tk()
        self.root.title("Futures Grid Trading Bot")
        self.root.geometry("1200x800")
        
        # Load saved configuration
        self.config = ConfigManager.load_config()
        
        self.exchange = None
        self.symbol = 'BTC/USD:USD'  # Updated to Phemex default
        self.positions = []
        self.orders = []
        self.grid_levels = []
        self.is_running = False
        
        # Trading parameters
        self.grid_size = 10  # Number of grid levels
        self.grid_spacing = 1.0  # Percentage between grid levels
        self.position_size = 100  # Size of each grid position in USDT
        self.take_profit = 2.0  # Take profit percentage
        self.leverage = 1  # Default leverage
        
        # PnL tracking
        self.total_fees = 0
        self.realized_pnl = 0
        self.start_balance = 0
        self.trade_history = []
        
        # Available exchanges and their configurations
        self.exchange_configs = {
            'Phemex': {
                'id': 'phemex',
                'markets': ['BTC/USD:USD', 'ETH/USD:USD', 'SOL/USD:USD'],
                'type': 'future',
                'maker_fee': 0.0001,
                'taker_fee': 0.0006
            }
        }
        
        # Create configuration variables
        self.setup_gui_variables()
        
        # Initialize GUI
        self.setup_gui()
        
        # Populate saved API configurations if available
        if self.config:
            saved_exchange = self.config.get('last_exchange')
            saved_api_key = self.config.get('api_key', '')
            
            if saved_exchange and saved_exchange in self.exchange_configs:
                self.exchange_var.set(saved_exchange)
                self.api_key_var.set(saved_api_key)
        
        # Start account overview updates
        self.update_account_overview()

    def draw_status_indicator(self, status):
        """Draw connection status indicator"""
        self.status_canvas.delete("all")
        
        if status == "connected":
            # Green circle for connected
            self.status_canvas.create_oval(2, 2, 18, 18, 
                                         fill='#4CAF50', 
                                         outline='#4CAF50')
            # Checkmark
            self.status_canvas.create_line(5, 10, 8, 13, 
                                         fill='white', 
                                         width=2)
            self.status_canvas.create_line(8, 13, 15, 6, 
                                         fill='white', 
                                         width=2)
        elif status == "connecting":
            # Yellow circle for connecting
            self.status_canvas.create_oval(2, 2, 18, 18, 
                                         fill='#FFC107', 
                                         outline='#FFC107')
            # Loading dots
            for i in range(3):
                x = 7 + i * 3
                self.status_canvas.create_oval(x, 9, x+2, 11, 
                                            fill='white', 
                                            outline='white')
        else:  # disconnected
            # Red circle for disconnected
            self.status_canvas.create_oval(2, 2, 18, 18, 
                                         fill='#FF5252', 
                                         outline='#FF5252')
            # X mark
            self.status_canvas.create_line(6, 6, 14, 14, 
                                         fill='white', 
                                         width=2)
            self.status_canvas.create_line(6, 14, 14, 6, 
                                         fill='white', 
                                         width=2)

    def setup_gui_variables(self):
        """Set up Tkinter variables after root window creation"""
        # Exchange selection variable
        self.exchange_var = tk.StringVar(self.root, value="Phemex")
        
        # API configuration variables
        self.api_key_var = tk.StringVar(self.root)
        self.api_secret_var = tk.StringVar(self.root)
        
        # Market selection variable
        self.market_var = tk.StringVar(self.root, value='BTC/USD:USD')
        
        # Grid configuration variables
        self.upper_price_var = tk.StringVar(self.root)
        self.lower_price_var = tk.StringVar(self.root)
        self.num_grids_var = tk.StringVar(self.root, value='10')
        self.investment_var = tk.StringVar(self.root, value='100')
        self.leverage_var = tk.StringVar(self.root, value='1')
        self.direction_var = tk.StringVar(self.root, value='Long')

    def setup_grid_section(self, main_container):
        """Create Grid Configuration Section"""
        # Grid Configuration Frame
        grid_frame = ttk.Frame(main_container, padding="10", style='Grid.TFrame')
        grid_frame.pack(fill=tk.X, pady=(5, 10))
        
        # Grid Configuration Header
        ttk.Label(grid_frame,
                 text="GRID CONFIGURATION",
                 font=('Consolas', 14, 'bold'),
                 foreground='#2196F3').pack(anchor=tk.W)
        
        # Grid Configuration Container
        grid_config_container = ttk.Frame(grid_frame)
        grid_config_container.pack(fill=tk.X, pady=(5, 0))
        
        # Price Range
        price_frame = ttk.Frame(grid_config_container)
        price_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(price_frame, 
                 text="Lower Price:", 
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(0, 10))
        lower_price_entry = ttk.Entry(price_frame, 
                                    textvariable=self.lower_price_var, 
                                    width=10)
        lower_price_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(price_frame, 
                 text="Upper Price:", 
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(20, 10))
        upper_price_entry = ttk.Entry(price_frame, 
                                    textvariable=self.upper_price_var, 
                                    width=10)
        upper_price_entry.pack(side=tk.LEFT, padx=5)
        
        # Number of Grids and Investment
        grid_settings_frame = ttk.Frame(grid_config_container)
        grid_settings_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(grid_settings_frame, 
                 text="Num Grids:", 
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(0, 10))
        num_grids_entry = ttk.Entry(grid_settings_frame, 
                                  textvariable=self.num_grids_var, 
                                  width=5)
        num_grids_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(grid_settings_frame, 
                 text="Investment:", 
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(20, 10))
        investment_entry = ttk.Entry(grid_settings_frame, 
                                   textvariable=self.investment_var, 
                                   width=10)
        investment_entry.pack(side=tk.LEFT, padx=5)
        
        # Leverage and Direction
        leverage_frame = ttk.Frame(grid_config_container)
        leverage_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(leverage_frame, 
                 text="Leverage:", 
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(0, 10))
        leverage_entry = ttk.Entry(leverage_frame, 
                                 textvariable=self.leverage_var, 
                                 width=5)
        leverage_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(leverage_frame, 
                 text="Direction:", 
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(20, 10))
        direction_dropdown = ttk.Combobox(leverage_frame, 
                                        textvariable=self.direction_var, 
                                        values=['Long', 'Short'], 
                                        state="readonly", 
                                        width=10)
        direction_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Buttons for preview and create
        button_frame = ttk.Frame(grid_config_container)
        button_frame.pack(side=tk.RIGHT, padx=20)
        
        preview_button = ttk.Button(button_frame, 
                                  text="Preview Grid", 
                                  command=self.preview_grid)
        preview_button.pack(side=tk.LEFT, padx=5)
        
        create_button = ttk.Button(button_frame, 
                                 text="Create Grid Bot", 
                                 command=self.create_grid_bot)
        create_button.pack(side=tk.LEFT, padx=5)
        
        # Close Positions Button
        close_button = ttk.Button(button_frame, 
                                text="Close All Positions", 
                                command=self.close_all_positions)
        close_button.pack(side=tk.LEFT, padx=5)

    def setup_gui(self):
        # Set dark theme colors
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # Configure colors
        bg_color = '#121212'  # Dark background
        text_color = '#E0E0E0'  # Light text
        accent_color = '#2196F3'  # Bloomberg-like blue
        header_color = '#1E1E1E'  # Slightly lighter than background
        
        self.root.configure(bg=bg_color)
        
        # Configure styles
        self.style.configure('TFrame', background=bg_color)
        self.style.configure('TLabel', 
                           background=bg_color, 
                           foreground=text_color,
                           font=('Consolas', 10))
        self.style.configure('TButton', 
                           background=accent_color,
                           foreground=text_color,
                           font=('Consolas', 10))
        self.style.configure('TEntry', 
                           fieldbackground=header_color,
                           foreground=text_color,
                           insertcolor=text_color,
                           font=('Consolas', 10))
        
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 1. EXCHANGE CONFIGURATION SECTION (First)
        exchange_frame = ttk.Frame(main_container, padding="10")
        exchange_frame.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(exchange_frame,
                 text="EXCHANGE CONFIGURATION",
                 font=('Consolas', 14, 'bold'),
                 foreground='#2196F3').pack(anchor=tk.W)
        
        # Exchange selection and API config container
        config_container = ttk.Frame(exchange_frame)
        config_container.pack(fill=tk.X, pady=(5, 0))
        
        # Left side - Exchange selection
        exchange_select_frame = ttk.Frame(config_container)
        exchange_select_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(exchange_select_frame,
                 text="Exchange:",
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(0, 10))
        
        exchange_dropdown = ttk.Combobox(exchange_select_frame,
                                       textvariable=self.exchange_var,
                                       values=list(self.exchange_configs.keys()),
                                       state="readonly",
                                       width=15)
        exchange_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Create market selection dropdown
        ttk.Label(exchange_select_frame,
                 text="Market:",
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(20, 10))
        
        market_dropdown = ttk.Combobox(exchange_select_frame,
                                     textvariable=self.market_var,
                                     values=self.exchange_configs['Phemex']['markets'],
                                     state="readonly",
                                     width=15)
        market_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Center - API Configuration
        api_frame = ttk.Frame(config_container)
        api_frame.pack(side=tk.LEFT, padx=20, fill=tk.X, expand=True)
        
        ttk.Label(api_frame,
                 text="API Key:",
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(0, 10))
        
        api_key_entry = ttk.Entry(api_frame,
                                textvariable=self.api_key_var,
                                width=30)
        api_key_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(api_frame,
                 text="Secret:",
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(20, 10))
        
        api_secret_entry = ttk.Entry(api_frame,
                                   textvariable=self.api_secret_var,
                                   width=30,
                                   show="•")
        api_secret_entry.pack(side=tk.LEFT, padx=5)
        
        # Right side - Connection status and button
        connect_frame = ttk.Frame(config_container)
        connect_frame.pack(side=tk.RIGHT, padx=20)
        
        # Status indicator
        self.status_canvas = tk.Canvas(connect_frame,
                                     width=20,
                                     height=20,
                                     bg='#121212',
                                     highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=5)
        self.draw_status_indicator("disconnected")
        
        # Connect button
        self.connect_button = ttk.Button(connect_frame,
                                       text="Connect",
                                       command=self.test_connection,
                                       style='Connect.TButton')
        self.connect_button.pack(side=tk.LEFT, padx=5)

        # 2. ACCOUNT OVERVIEW SECTION
        account_frame = ttk.Frame(main_container, padding="10")
        account_frame.pack(fill=tk.X, pady=(5, 10))
        
        # Account Overview Header
        ttk.Label(account_frame,
                 text="ACCOUNT OVERVIEW",
                 font=('Consolas', 14, 'bold'),
                 foreground='#2196F3').pack(anchor=tk.W)
        
        # Balance display frame
        balance_frame = ttk.Frame(account_frame)
        balance_frame.pack(fill=tk.X, pady=(5, 0))
        
        # USDT Balance
        balance_left = ttk.Frame(balance_frame)
        balance_left.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(balance_left,
                 text="Futures Balance:",
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(0, 10))
                 
        self.balance_label = ttk.Label(balance_left,
                                     text="0.00 USD",
                                     font=('Consolas', 11, 'bold'),
                                     foreground='#4CAF50')
        self.balance_label.pack(side=tk.LEFT)
        
        # Positions Value
        balance_middle = ttk.Frame(balance_frame)
        balance_middle.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(balance_middle,
                 text="Open Positions Value:",
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(0, 10))
                 
        self.positions_value_label = ttk.Label(balance_middle,
                                             text="0.00 USD",
                                             font=('Consolas', 11, 'bold'),
                                             foreground='#2196F3')
        self.positions_value_label.pack(side=tk.LEFT)
        
        # Total PnL
        balance_right = ttk.Frame(balance_frame)
        balance_right.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(balance_right,
                 text="Total PnL (incl. fees):",
                 font=('Consolas', 11)).pack(side=tk.LEFT, padx=(0, 10))
                 
        self.total_pnl_label = ttk.Label(balance_right,
                                        text="0.00 USD",
                                        font=('Consolas', 11, 'bold'),
                                        foreground='#4CAF50')
        self.total_pnl_label.pack(side=tk.LEFT)
        
        # 3. GRID CONFIGURATION SECTION
        self.setup_grid_section(main_container)
        
        # Status text area
        self.status_text = tk.Text(main_container, 
                                 height=8,
                                 bg='#1E1E1E',
                                 fg='#E0E0E0',
                                 font=('Consolas', 10))
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=10)
        self.status_text.tag_configure('timestamp', foreground='#2196F3')

    def log(self, message):
        """Log message with timestamp"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(self, 'status_text'):
                self.status_text.insert(tk.END, timestamp, 'timestamp')
                self.status_text.insert(tk.END, f": {message}\n")
                self.status_text.see(tk.END)
            else:
                print(f"{timestamp}: {message}")
        except Exception as e:
            print(f"Logging error: {e}")
            print(f"Message was: {message}")

    def test_connection(self):
        """Test the API connection with current credentials"""
        self.draw_status_indicator("connecting")
        self.connect_button.config(state='disabled')
        
        def connect():
            try:
                exchange_config = self.exchange_configs['Phemex']
                exchange = getattr(ccxt, exchange_config['id'])({
                    'enableRateLimit': True,
                    'apiKey': self.api_key_var.get(),
                    'secret': self.api_secret_var.get()
                })
                
                # Test authentication
                exchange.fetch_balance()
                
                # Save configuration
                config = {
                    'last_exchange': 'Phemex',
                    'api_key': self.api_key_var.get()
                }
                ConfigManager.save_config(config)
                
                # Update status
                def success_callback():
                    self.draw_status_indicator("connected")
                    self.log("API connection successful")
                    self.connect_button.config(state='normal')
                
                self.root.after(0, success_callback)
                
                # Store working exchange instance
                self.exchange = exchange
                self.symbol = self.market_var.get()
                
            except Exception as e:
                error_message = str(e)
                def error_callback():
                    self.draw_status_indicator("disconnected")
                    self.log(f"API connection failed: {error_message}")
                    self.connect_button.config(state='normal')
                
                self.root.after(0, error_callback)
                self.exchange = None
        
        # Run connection test in separate thread
        threading.Thread(target=connect, daemon=True).start()

    def update_account_overview(self):
        """Update account balance, positions value, and PnL display"""
        try:
            if not self.exchange:
                self.balance_label.config(text="Not Connected")
                self.positions_value_label.config(text="Not Connected")
                self.total_pnl_label.config(text="Not Connected")
                return
                
            # Fetch futures balance
            balance = self.exchange.fetch_balance()
            usdt_balance = balance.get('USD', {}).get('total', 0)
            self.balance_label.config(text=f"{usdt_balance:.2f} USD")
            
            # Store initial balance if not set
            if self.start_balance == 0:
                self.start_balance = usdt_balance
            
            # Calculate total positions value and unrealized PnL
            positions = self.exchange.fetch_positions([self.symbol])
            total_value = 0
            unrealized_pnl = 0
            for position in positions:
                if float(position['contracts']) > 0:
                    total_value += float(position['notional'])
                    unrealized_pnl += float(position['unrealizedPnl'])
                    
            self.positions_value_label.config(text=f"{total_value:.2f} USD")
            
            # Calculate total PnL including fees
            total_pnl = self.realized_pnl + unrealized_pnl - self.total_fees
            
            # Update PnL label with color based on profit/loss
            if total_pnl > 0:
                self.total_pnl_label.config(text=f"+{total_pnl:.2f} USD", foreground='#4CAF50')
            else:
                self.total_pnl_label.config(text=f"{total_pnl:.2f} USD", foreground='#FF5252')
            
            # Update every 10 seconds
            self.root.after(10000, self.update_account_overview)
            
        except Exception as e:
            self.log(f"Error updating account overview: {str(e)}")
            self.balance_label.config(text="Error")
            self.positions_value_label.config(text="Error")
            self.total_pnl_label.config(text="Error")

    def preview_grid(self):
        """Preview grid levels and investment details before creating bot"""
        try:
            # Get and validate parameters
            upper_price = float(self.upper_price_var.get())
            lower_price = float(self.lower_price_var.get())
            num_grids = int(self.num_grids_var.get())
            total_investment = float(self.investment_var.get())
            leverage = int(self.leverage_var.get())
            direction = self.direction_var.get()
            
            if upper_price <= lower_price:
                raise ValueError("Upper price must be greater than lower price")
            
            if num_grids < 2:
                raise ValueError("Number of grids must be at least 2")
                
            # Calculate grid levels
            price_diff = upper_price - lower_price
            grid_step = price_diff / (num_grids - 1)
            investment_per_grid = total_investment / num_grids
            
            # Preview calculations
            self.log("\n=== Grid Preview ===")
            self.log(f"Direction: {direction}")
            self.log(f"Price Range: {lower_price:.2f} - {upper_price:.2f} USD")
            self.log(f"Grid Step: {grid_step:.2f} USD")
            self.log(f"Number of Grids: {num_grids}")
            self.log(f"Total Investment: {total_investment:.2f} USD")
            self.log(f"Investment per Grid: {investment_per_grid:.2f} USD")
            self.log(f"Leverage: {leverage}x")
            
            # Preview grid levels
            self.log("\nGrid Levels:")
            for i in range(num_grids):
                price = upper_price - (i * grid_step)
                size = (investment_per_grid * leverage) / price
                self.log(f"Level {i+1}: {price:.2f} USD - Size: {size:.4f}")
                
        except ValueError as e:
            self.log(f"Error in parameters: {str(e)}")
        except Exception as e:
            self.log(f"Error creating preview: {str(e)}")

    def create_grid_bot(self):
        """Create and start the grid bot with specified parameters"""
        try:
            if not self.exchange:
                raise ValueError("Please connect to exchange first")
                
            # Get and validate parameters
            upper_price = float(self.upper_price_var.get())
            lower_price = float(self.lower_price_var.get())
            num_grids = int(self.num_grids_var.get())
            total_investment = float(self.investment_var.get())
            leverage = int(self.leverage_var.get())
            direction = self.direction_var.get()
            
            # Set leverage on exchange
            try:
                if hasattr(self.exchange, 'fapiPrivate_post_leverage'):
                    self.exchange.fapiPrivate_post_leverage({
                        'symbol': self.symbol.replace('/', '').replace(':USD', ''),
                        'leverage': leverage
                    })
                elif hasattr(self.exchange, 'set_leverage'):
                    self.exchange.set_leverage(leverage, self.symbol)
            except Exception as e:
                self.log(f"Warning setting leverage: {str(e)}")
            
            # Calculate grid levels
            price_diff = upper_price - lower_price
            grid_step = price_diff / (num_grids - 1)
            investment_per_grid = total_investment / num_grids
            
            self.log("\n=== Creating Grid Bot ===")
            self.log(f"Setting up {direction} grid...")
            
            # Get exchange fee rates
            exchange_config = self.exchange_configs['Phemex']
            maker_fee = exchange_config['maker_fee']
            
            # Create orders for each grid level
            self.grid_levels = []
            for i in range(num_grids):
                price = upper_price - (i * grid_step)
                size = (investment_per_grid * leverage) / price
                
                try:
                    if direction == "Long":
                        order = self.exchange.create_limit_buy_order(
                            self.symbol,
                            size,
                            price
                        )
                    else:  # Short
                        order = self.exchange.create_limit_sell_order(
                            self.symbol,
                            size,
                            price
                        )
                    
                    # Calculate and track fees
                    order_value = size * price
                    fee = order_value * maker_fee
                    self.total_fees += fee
                    
                    self.grid_levels.append({
                        'price': price,
                        'size': size,
                        'order': order,
                        'type': 'buy' if direction == "Long" else 'sell',
                        'fee': fee
                    })
                    
                    self.log(f"Created {direction} order at {price:.2f} USD (Fee: {fee:.4f} USD)")
                    
                except Exception as e:
                    self.log(f"Error creating order at {price:.2f}: {str(e)}")
                    
            self.log(f"Initial total fees: {self.total_fees:.4f} USD")
            self.log("Grid bot created successfully!")
            
        except ValueError as e:
            self.log(f"Error: {str(e)}")
        except Exception as e:
            self.log(f"Error creating grid bot: {str(e)}")

    def close_all_positions(self):
        """Close all open positions and cancel all pending orders"""
        try:
            if not self.exchange:
                raise ValueError("Please connect to exchange first")
                
            self.log("\n=== Closing All Positions ===")
            
            # Cancel all pending orders
            open_orders = self.exchange.fetch_open_orders(self.symbol)
            for order in open_orders:
                try:
                    self.exchange.cancel_order(order['id'], self.symbol)
                    self.log(f"Cancelled order at {order['price']}")
                except Exception as e:
                    self.log(f"Error cancelling order: {str(e)}")
            
            # Close all open positions
            positions = self.exchange.fetch_positions([self.symbol])
            for position in positions:
                if float(position['contracts']) > 0:
                    try:
                        if position['side'] == 'long':
                            self.exchange.create_market_sell_order(
                                self.symbol,
                                position['contracts']
                            )
                        else:
                            self.exchange.create_market_buy_order(
                                self.symbol,
                                position['contracts']
                            )
                        self.log(f"Closed {position['side']} position of {position['contracts']} contracts")
                    except Exception as e:
                        self.log(f"Error closing position: {str(e)}")
            
            self.grid_levels = []
            self.log("All positions and orders cancelled")
            
        except Exception as e:
            self.log(f"Error closing positions: {str(e)}")

def main():
    bot = GridTradingBot()
    bot.root.mainloop()

if __name__ == "__main__":
    main()