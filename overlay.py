import tkinter as tk
from win32api import GetSystemMetrics
import win32gui
import threading
import time

hud_color = "#ff0ff0"
snap_line = "#ffc000"
crh_color = "#00ff00"
crh_size = 7

class MoveableOverlay(tk.Tk):
    def __init__(self, target_process_name):
        super().__init__()

        self.target_process_name = target_process_name
        self.target_window_handle = self.find_target_window()

        if not self.target_window_handle:
            print(f"Target window with name '{target_process_name}' not found!")
            self.destroy()
            return

        self.crosshair_radius_cm = crh_size  # Desired crosshair radius in centimeters
        self.crosshair_length = int(self.crosshair_radius_cm * 2)  # Set line length to twice the desired radius

        self.geometry(f"{GetSystemMetrics(0)}x{GetSystemMetrics(1)}+0+0")
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-transparentcolor', 'black')

        self.canvas = tk.Canvas(self, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.crosshair_h = None
        self.crosshair_v = None
        self.snap_line = None  # New line for snap

        self.update_crosshair()

        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.on_drag)

        self.dragging = False

        # Start a separate thread to periodically update the crosshair
        self.update_thread = threading.Thread(target=self.periodic_update)
        self.update_thread.daemon = True
        self.update_thread.start()

        # Bind to the Destroy event
        self.bind("<Destroy>", self.on_destroy)

    def find_target_window(self):
        return win32gui.FindWindow(None, self.target_process_name)

    def draw_crosshair(self, window_rect):
        x = (window_rect[0] + window_rect[2]) // 2
        y = (window_rect[1] + window_rect[3]) // 2

        # Draw horizontal line
        self.crosshair_h = self.canvas.create_line(x - self.crosshair_length, y, x + self.crosshair_length, y, fill=crh_color, width=2)

        # Draw vertical line
        self.crosshair_v = self.canvas.create_line(x, y - self.crosshair_length, x, y + self.crosshair_length, fill=crh_color, width=2)

        # Draw line from bottom center to crosshair middle
        bottom_center_x = GetSystemMetrics(0) // 2
        bottom_center_y = GetSystemMetrics(1)
        self.snap_line = self.canvas.create_line(bottom_center_x, bottom_center_y, x, y, fill=snap_line, width=2)

    def update_crosshair(self):
        window_rect = self.get_target_window_rect()
        if window_rect:
            is_minimized = win32gui.IsIconic(self.target_window_handle)
            if is_minimized:
                self.canvas.delete("all")  # Clear all drawings when minimized
            else:
                self.canvas.delete(self.crosshair_h)
                self.canvas.delete(self.crosshair_v)
                self.canvas.delete(self.snap_line)  # Clear previous snap line
                self.draw_crosshair(window_rect)

    def get_target_window_rect(self):
        try:
            rect = win32gui.GetWindowRect(self.target_window_handle)
            return rect
        except Exception:
            return None

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y
        self.dragging = True

    def on_drag(self, event):
        if self.dragging:
            deltax = event.x - self.x
            deltay = event.y - self.y
            self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")

    def stop_drag(self, event):
        self.dragging = False

    def periodic_update(self):
        # Periodically update the crosshair in the background
        while self.target_window_exists():
            time.sleep(0.03)  # Adjust the interval as needed
            self.update_crosshair()

    def target_window_exists(self):
        return win32gui.IsWindow(self.target_window_handle)

    def on_destroy(self, event):
        # Additional cleanup code when the window is destroyed
        print("Application is closing. Clean up resources here.")

if __name__ == "__main__":
    app = MoveableOverlay("Rechner")
    app.mainloop()
