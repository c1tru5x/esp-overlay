import tkinter as tk
from win32api import GetSystemMetrics
import win32gui
import win32con
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
        self.target_window_handles = self.find_target_windows()

        if not self.target_window_handles:
            print(f"No windows found with name '{target_process_name}'")
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

        self.crosshair_h = {}
        self.crosshair_v = {}
        self.snap_line = {}
        self.text_id = {}

        self.update_crosshair()

        # Start a separate thread to periodically update the crosshair
        self.update_thread = threading.Thread(target=self.periodic_update)
        self.update_thread.daemon = True
        self.update_thread.start()

        # Bind to window resize events
        self.old_window_proc = win32gui.SetWindowLong(self.winfo_id(), win32con.GWL_WNDPROC, self.on_size)

        # Bind to the Destroy event
        self.bind("<Destroy>", self.on_destroy)

    def find_target_windows(self):
        windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and self.target_process_name.lower() in win32gui.GetWindowText(hwnd).lower():
                windows.append(hwnd)
            return True

        win32gui.EnumWindows(callback, 0)
        return windows

    def draw_crosshair(self, window_rect, window_handle):
        x = (window_rect[0] + window_rect[2]) // 2
        y = (window_rect[1] + window_rect[3]) // 2

        # Draw horizontal line
        self.crosshair_h[window_handle] = self.canvas.create_line(x - self.crosshair_length, y, x + self.crosshair_length, y, fill=crh_color, width=2)

        # Draw vertical line
        self.crosshair_v[window_handle] = self.canvas.create_line(x, y - self.crosshair_length, x, y + self.crosshair_length, fill=crh_color, width=2)

        # Draw line from bottom center to crosshair middle
        bottom_center_x = GetSystemMetrics(0) // 2
        bottom_center_y = GetSystemMetrics(1)
        self.snap_line[window_handle] = self.canvas.create_line(bottom_center_x, bottom_center_y, x, y, fill=snap_line, width=2)

    def draw_hud_text(self, window_handle, lines):
        screen_width = GetSystemMetrics(0)
        text = "\n".join(lines)
        text_id = self.canvas.create_text(screen_width // 2, 150, text=text, font=("Arial", 8, "bold"), fill=hud_color)
        self.text_id[window_handle] = text_id

    def update_crosshair(self):
        for window_handle in self.target_window_handles:
            window_rect = self.get_target_window_rect(window_handle)
            if window_rect:
                is_minimized = win32gui.IsIconic(window_handle)
                if is_minimized:
                    self.canvas.delete("all")  # Clear all drawings when minimized
                else:
                    self.canvas.delete(self.crosshair_h.get(window_handle, 0))
                    self.canvas.delete(self.crosshair_v.get(window_handle, 0))
                    self.canvas.delete(self.snap_line.get(window_handle, 0))

                    # Draw crosshair and snap line
                    self.draw_crosshair(window_rect, window_handle)

                    # Draw HUD text with multiple lines for each window
                    lines = [
                        "--OVERLAY-- v1.0",
                        "Made by c1tru5x",
                        "in Python"
                    ]
                    if self.text_id.get(window_handle):
                        self.canvas.delete(self.text_id[window_handle])  # Clear previous text
                    self.draw_hud_text(window_handle, lines)

    def get_target_window_rect(self, window_handle):
        try:
            rect = win32gui.GetWindowRect(window_handle)
            return rect
        except Exception:
            return None

    def periodic_update(self):
        # Periodically update the crosshair in the background
        while self.target_windows_exist():
            time.sleep(0.03)  # Adjust the interval as needed
            self.update_crosshair()

    def target_windows_exist(self):
        return all(win32gui.IsWindow(handle) for handle in self.target_window_handles)

    def on_size(self, hwnd, msg, wparam, lparam):
        # Handle window size change
        if msg == win32con.WM_SIZE:
            self.update_crosshair()
        return win32gui.CallWindowProc(self.old_window_proc, hwnd, msg, wparam, lparam)

    def on_destroy(self, event):
        # Additional cleanup code when the window is destroyed
        print("Application is closing. Clean up resources here.")
        self.update_thread.join()

if __name__ == "__main__":
    app = MoveableOverlay("Rechner")
    app.mainloop()
