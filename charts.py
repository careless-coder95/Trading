"""
📊 CHART GENERATOR
ForexBot Pro - Performance Charts
"""

import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import List, Dict

class ChartGenerator:
    """Generate performance charts"""

    def __init__(self):
        self.chart_dir = "data/charts"
        os.makedirs(self.chart_dir, exist_ok=True)
        plt.style.use('dark_background')

    def generate_equity_curve(self, user_id: int, trades: List[Dict], initial_balance: float) -> str:
        """Generate equity curve chart"""
        try:
            if not trades:
                return None

            dates = []
            equity = []
            running_equity = initial_balance

            for trade in trades:
                exit_time = trade.get("exit_time")
                if exit_time:
                    try:
                        date_obj = datetime.fromisoformat(exit_time)
                        dates.append(date_obj)
                        running_equity += trade["profit_loss"]
                        equity.append(running_equity)
                    except:
                        continue

            if not dates:
                return None

            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(dates, equity, color='#00D9FF', linewidth=2, label='Equity')
            ax.fill_between(dates, equity, initial_balance, alpha=0.3, color='#00D9FF')
            ax.axhline(y=initial_balance, color='#FFD700', linestyle='--', linewidth=1, label='Initial Balance')
            
            ax.set_title('📈 Equity Curve', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Equity ($)', fontsize=12)
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            
            # Format dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            filepath = os.path.join(self.chart_dir, f"equity_{user_id}.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
            plt.close()
            
            return filepath
        except Exception as e:
            print(f"Chart error: {e}")
            return None

    def generate_monthly_bar(self, user_id: int, trades: List[Dict], title: str = "Monthly P&L") -> str:
        """Generate monthly P&L bar chart"""
        try:
            if not trades:
                return None

            # Calculate daily P&L
            daily_pnl = {}
            for trade in trades:
                exit_time = trade.get("exit_time")
                if exit_time:
                    try:
                        date_str = exit_time[:10]  # Get YYYY-MM-DD
                        if date_str not in daily_pnl:
                            daily_pnl[date_str] = 0
                        daily_pnl[date_str] += trade["profit_loss"]
                    except:
                        continue

            if not daily_pnl:
                return None

            dates = sorted(daily_pnl.keys())
            values = [daily_pnl[d] for d in dates]
            colors = ['#00FF00' if v >= 0 else '#FF0000' for v in values]

            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.bar(range(len(dates)), values, color=colors, alpha=0.8)
            ax.axhline(y=0, color='white', linestyle='-', linewidth=0.5)
            
            ax.set_title(f'📊 {title}', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('P&L ($)', fontsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Set x-axis labels
            if len(dates) > 15:
                step = len(dates) // 10
                ax.set_xticks(range(0, len(dates), step))
                ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45)
            else:
                ax.set_xticks(range(len(dates)))
                ax.set_xticklabels(dates, rotation=45)
            
            plt.tight_layout()
            
            filepath = os.path.join(self.chart_dir, f"monthly_{user_id}.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
            plt.close()
            
            return filepath
        except Exception as e:
            print(f"Chart error: {e}")
            return None

    def generate_pie_chart(self, user_id: int, data: Dict, title: str) -> str:
        """Generate pie chart for win/loss distribution"""
        try:
            fig, ax = plt.subplots(figsize=(8, 8))
            
            labels = list(data.keys())
            values = list(data.values())
            colors = ['#00FF00', '#FF0000', '#FFD700'][:len(labels)]
            
            ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, 
                   startangle=90, textprops={'fontsize': 12})
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            plt.tight_layout()
            
            filepath = os.path.join(self.chart_dir, f"pie_{user_id}.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#1a1a1a')
            plt.close()
            
            return filepath
        except Exception as e:
            print(f"Chart error: {e}")
            return None
