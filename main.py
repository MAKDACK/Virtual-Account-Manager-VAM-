from multiprocessing import process
import os
from sqlite3 import Time
import sys
import tkinter as tk
import customtkinter as ctk
import subprocess
import time
from PIL import Image, ImageTk, ImageDraw
import pygetwindow as gw
import psutil
import ctypes


class App:
    def __init__(self):
        # ------------------ Window ------------------
        self.window = tk.Tk()
        self.window.geometry("1168x712")
        self.window.configure(bg="#0b0b0d")
        self.window.title("Account Manager")
        self.window.resizable(False, False)

        # ------------------ Canvas ------------------
        self.canvas = tk.Canvas(
            self.window,
            bg="#0b0b0d",
            width=1168,
            height=712,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        self.activeAccounts = 0

        # ------------------ Page Item Lists ------------------
        self.dashItems = []    # Canvas shapes/text
        self.dashButtons = []  # Buttons
        self.dashVisible = True

        self.accountItems = []
        self.accountButtons = []
        self.accountVisible = False

        self.settingItems = []
        self.settingButtons = []
        self.settingVisible = False

        self.autoItems = []
        self.autoButtons = []
        self.autoVisible = False

        self.statusItems = []

        # ------------------ Backend ------------------
        #start with temp default paths
        self.shortcuts = {
            "Main": "",
            "Reroller": "",
            "Rimuru": ""
        }

        self.config_file = os.path.join(os.path.dirname(__file__), "shortcuts.txt")
        self.loadPaths()

        
        self.user32 = ctypes.windll.user32
        self.pid = ctypes.c_ulong()

        # ------------------ Build UI ------------------
        self.drawLayout()
        self.drawHeader()
        self.drawStatus()
        self.drawButtons()
        self.drawDash()

        self.processes = {}

    # ------------------ Helpers ------------------
    def load_asset(self, path):
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "assets", path)

    def flatButton(self, **kwargs):
        return tk.Button(
            self.window,
            relief="flat",
            bd=0,
            highlightthickness=0,
            takefocus=0,
            activebackground=self.window["bg"],
            activeforeground=None,
            **kwargs
        )

    def roundRect(self, x1, y1, x2, y2, radius=18, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def profileCircleWithBorder(self, path, size, border_color="grey", border_width=2, fill_color="#222222"):
        scale = 4
        large_size = (size[0]*scale, size[1]*scale)
        img = Image.new("RGBA", large_size, (0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0,0,large_size[0]-1, large_size[1]-1),
                     fill=fill_color, 
                     outline=border_color, 
                     width=border_width*scale
        )
        profile_img = Image.open(path).resize((large_size[0]-2*border_width*scale, large_size[1]-2*border_width*scale), Image.Resampling.LANCZOS).convert("RGBA")
        mask = Image.new("L", profile_img.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0,0,profile_img.size[0], profile_img.size[1]), fill=255)
        img.paste(profile_img, (border_width*scale, border_width*scale), mask)
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)

    # ------------------ Page visibility ------------------
    def clearCurrentPage(self):
        # Hide dashboard
        if self.dashVisible:
            for item in self.dashItems:
                self.canvas.itemconfigure(item, state='hidden')
            for btn in self.dashButtons:
                btn.place_forget()
            self.dashVisible = False

        # Hide account page
        if self.accountVisible:
            for item in self.accountItems:
                self.canvas.itemconfigure(item, state='hidden')
            for btn in self.accountButtons:
                btn.place_forget()
            self.accountVisible = False

        # Hide settings
        if self.settingVisible:
            for item in self.settingItems:
                self.canvas.itemconfigure(item, state='hidden')
            for btn in self.settingButtons:
                btn.place_forget()
            self.settingVisible = False

        # Hide automation
        if self.autoVisible:
            for item in self.autoItems:
                self.canvas.itemconfigure(item, state='hidden')
            for btn in self.autoButtons:
                btn.place_forget()
            self.autoVisible = False

    def showDash(self):
        if self.dashVisible:
            return
        for item in self.dashItems:
            self.canvas.itemconfigure(item, state='normal')
        # Re-place buttons
        positions = [(391,185), (574,184), (956,64), (395,343), (644,343), (894,343), (381,393), (630,393), (880,393)]
        for i, btn in enumerate(self.dashButtons):
            x, y = positions[i]
            btn.place(x=x, y=y)
        self.dashVisible = True

    def showSettings(self):
        if self.settingVisible:
            return
        if self.settingButtons == []:
            self.settingVisible = True
            return self.drawSettings()
        for item in self.settingItems:
            self.canvas.itemconfigure(item, state='normal')
        positions = [(742,108), (742,166), (742,224)]
        for i, btn in enumerate(self.settingButtons):
            x, y = positions[i]
            btn.place(x=x, y=y, width=152, height=41)
            print(x, y)
        self.settingVisible = True

    def refreshStatus(self):
        for item in self.statusItems:
            self.canvas.delete(item)
        self.statusItems.clear()
        self.drawStatus()

    # ------------------ Custom Functions ------------------
    def runAccount(self, id):
        path = None
        if id == 1:
            path = self.shortcuts["Main"]
        elif id == 2:
            path = self.shortcuts["Reroller"]
        elif id == 3:
            path = self.shortcuts["Rimuru"]
        if not path:
            return

        # Get current windows before launching
        before_windows = set(gw.getAllTitles())

        # Launch the shortcut
        subprocess.Popen(path, shell=True)

        # Wait a bit for the window to appear
        time.sleep(3)

        # Get new windows
        after_windows = set(gw.getAllTitles())
        new_windows = after_windows - before_windows

        if new_windows:
            window_title = new_windows.pop()
            self.processes[id] = window_title
            print(f"Account {id} started. Window title: {window_title}")
        else:
            print(f"Could not detect window title for Account {id}")

        self.activeAccounts = self.checkStatus()
        self.refreshStatus()


    def stopAccount(self, id):
        # Get the exact window title that was stored when this account was started
        window_title = self.processes.get(id)
        if not window_title:
            print(f"No running window recorded for account {id}")
            return

        # Try to find the window with the exact title
        window = next((w for w in gw.getAllWindows() if w.title == window_title), None)
        if not window:
            print(f"Window '{window_title}' not found")
            return

        try:
            hwnd = window._hWnd
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(self.pid))
            process = psutil.Process(self.pid.value)
            process.terminate()  # or process.kill()
            print(f"Terminated account {id} with PID {self.pid.value}")
            # Remove from tracking dict
            del self.processes[id]
        except Exception as e:
            print(f"Failed to terminate account {id}: {e}")

    def checkStatus(self):
        try:
            output = subprocess.check_output(
                ['tasklist', '/FI', 'IMAGENAME eq HD-Player.exe'],
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode()

            if "HD-Player.exe" not in output:
                return 0

            # Count lines minus header
            return max(0, output.count("HD-Player.exe"))
        except Exception:
            return 0

    def runClients(self):
        self.refreshStatus()
        for shortcut in self.shortcuts.values():
            os.startfile(shortcut)
            time.sleep(2)

    def closeAccounts(self):
        subprocess.run(['taskkill', '/F', '/IM', 'HD-Player.exe'])
        self.activeAccounts = 0
        self.refreshStatus()

    def connectedDevices(self):
        subprocess.Popen(["adb", "devices"])

    def menuFunction(self, name):
        if name == "Dashboard":
            self.clearCurrentPage()
            self.showDash()
            print("Dashboard Clicked")
        elif name == "Accounts":
            self.clearCurrentPage()
            print("Accounts Clicked")
        elif name == "Automation":
            self.clearCurrentPage()
            print("Automation Clicked")
        elif name == "Settings":
            self.clearCurrentPage()
            self.showSettings()
            print("Settings Clicked")

    def setDir(self, accountID):
        if accountID == 1:
            path = tk.filedialog.askopenfilename(title="Select Shortcut for Account #1",
                                                 filetypes=[("Shortcut Files", "*.lnk")])
            if path:
                self.shortcuts["Main"] = path
                print(f"Account #1 path set to: {path}")
        elif accountID == 2:
            path = tk.filedialog.askopenfilename(title="Select Shortcut for Account #2",
                                                 filetypes=[("Shortcut Files", "*.lnk")])
            if path:
                self.shortcuts["Reroller"] = path
                print(f"Account #2 path set to: {path}")
        elif accountID == 3:
            path = tk.filedialog.askopenfilename(title="Select Shortcut for Account #3",
                                                 filetypes=[("Shortcut Files", "*.lnk")])
            if path:
                self.shortcuts["Rimuru"] = path
                print(f"Account #3 path set to: {path}")

        self.savePaths()

    def savePaths(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                for key, path in self.shortcuts.items():
                    f.write(f"{key}={path}\n")
            print("Paths saved successfully.")
        except Exception as e:
            print(f"Failed to save paths: {e}")

    def loadPaths(self):
        if not os.path.exists(self.config_file):
            print("No saved paths found, using defaults.")
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "=" not in line:
                        continue
                    key, path = line.split("=", 1)
                    if key in self.shortcuts and os.path.exists(path):
                        self.shortcuts[key] = path

            print("Paths loaded successfully.")
        except Exception as e:
            print(f"Failed to load paths: {e}")

    # ------------------ Layout ------------------
    def drawLayout(self):
        self.canvas.create_line(289, 0, 289, 861, fill="#222222", width=1)
        self.canvas.create_line(0, 88, 290, 88, fill="#222222", width=1)
        self.canvas.create_line(0, 621, 290, 621, fill="#222222", width=1)

    # ------------------ Header ------------------
    def drawHeader(self):
        x1, y1, x2, y2 = 24, 15, 80, 71
        width = x2 - x1
        height = y2 - y1
        bc = "#3A3A3A"
        self.circle_img = self.profileCircleWithBorder(
            "assets/profile.jpg", (width, height), border_color=bc, border_width=2, fill_color="#222222"
        )
        self.canvas.create_image(x1, y1, anchor="nw", image=self.circle_img)
        self.canvas.create_text(110, 26, anchor="nw",
            text="Game Manager", fill="#ffffff", font=("Inter", 16))
        self.canvas.create_text(110, 48, anchor="nw",
            text="Version: 0.0.1", fill="#8b8b8b", font=("Inter", 12))

    # ------------------ Status ------------------
    def drawStatus(self):
        t1 = self.canvas.create_text(42, 645, anchor="nw",
            text="Status", fill="#ffffff", font=("Inter", 12))
        t2 = self.canvas.create_text(208, 645, anchor="nw",
            text="Online", fill="#239a05", font=("Inter", 12))
        t3 = self.canvas.create_oval(192, 649, 200, 657, fill="#239a05", outline="")
        t4 = self.canvas.create_text(42, 672, anchor="nw",
            text="Active Accounts", fill="#ffffff", font=("Inter", 12))
        t5 = self.canvas.create_text(237, 672, anchor="nw",
            text=self.activeAccounts, fill="#ffffff", font=("Inter", 12))
        self.statusItems.extend([t1, t2, t3, t4, t5])

    # ------------------ Buttons ------------------
    def drawButtons(self):


        sidebar_buttons = [
            ("button.png", "Dashboard", 105),
            ("accountsbutton.png", "Accounts", 172),
            ("autobutton.png", "Automation", 239),
            ("settingsbutton.png", "Settings", 305),
        ]

        self.sidebar_imgs = []
        for img, name, y in sidebar_buttons:
            image = tk.PhotoImage(file=self.load_asset(img))
            self.sidebar_imgs.append(image)
            self.flatButton(image=image,
                command=lambda n=name: self.menuFunction(n)
            ).place(x=17, y=y, width=255, height=51)

    # ------------------ Cards ------------------
    def drawDash(self):
        # Canvas items


        self.dashItems.clear()
        rect1 = self.roundRect(371, 131, 1082, 239, fill="#1e1e1e", outline="")
        rect2 = self.roundRect(371, 276, 584, 450, fill="#1e1e1e", outline="")
        rect3 = self.roundRect(620, 276, 833, 450, fill="#1e1e1e", outline="")
        rect4 = self.roundRect(869, 276, 1082, 450, fill="#1e1e1e", outline="")
        text1 = self.canvas.create_text(399, 153, anchor="nw",
                                      text="Bulk Actions", fill="#ffffff", font=("Inter", 16))
        self.dashItems.extend([rect1, rect2, rect3, rect4, text1])

        text2 = self.canvas.create_text(412, 48, anchor="nw",
            text="Account Management", fill="#ffffff", font=("Inter", 24))
        text3 =self.canvas.create_text(412, 94, anchor="nw",
            text="Manage and control your game accounts with ease",
            fill="#8b8b8b", font=("Inter", 12))
        self.dashItems.extend([text2, text3])

        # Buttons
        self.dashButtons.clear()
        self.bulk_start_img = tk.PhotoImage(file=self.load_asset("powerbutton.png"))
        self.bulk_stop_img = tk.PhotoImage(file=self.load_asset("stopall.png"))
        btn_start = self.flatButton(image=self.bulk_start_img, bg="#1e1e1e", command=self.runClients)
        btn_start.place(x=391, y=185)
        btn_stop = self.flatButton(image=self.bulk_stop_img, bg="#1e1e1e", command=self.closeAccounts)
        btn_stop.place(x=574, y=184)
        self.dashButtons.extend([btn_start, btn_stop])

        self.addButtonImg = tk.PhotoImage(file=self.load_asset("addbutton.png"))
        btn1 = self.flatButton(image=self.addButtonImg,
            command=lambda: print("Add Account")
        )
        btn1.place(x=956, y=64, width=165, height=35)
        self.dashButtons.append(btn1)

        # Account buttons
        self.account_imgs = []
        for i, x in enumerate([395, 644, 894], start=1):
            img = tk.PhotoImage(file=self.load_asset("startone.png"))
            self.account_imgs.append(img)
            btn = self.flatButton(image=img, bg="#1e1e1e", command=lambda n=i: self.runAccount(n))
            btn.place(x=x-1, y=343, width=170, height=35)
            self.dashButtons.append(btn)

        # Stop buttons
        self.stopImgs = []
        for i, x in enumerate([395, 644, 894], start=1):
            img = tk.PhotoImage(file=self.load_asset("stopaccount.png"))
            self.stopImgs.append(img)
            btn = self.flatButton(image=img, command=lambda n=i: self.stopAccount(n))
            btn.place(x=x-14, y=393)
            self.dashButtons.append(btn)

        accText1 = self.canvas.create_text(408, 290, anchor="nw",
            text="Account #1", fill="#ffffff", font=("Inter", 24))
        accText2 = self.canvas.create_text(657, 290, anchor="nw",
            text="Account #2", fill="#ffffff", font=("Inter", 24))
        accText3 = self.canvas.create_text(906, 290, anchor="nw",
            text="Account #3", fill="#ffffff", font=("Inter", 24))
        self.dashItems.extend([accText1, accText2, accText3])

    def drawSettings(self):
        print("Loading Settings...")

        self.settingItems.clear()
        self.settingButtons.clear()

        pageTitle = self.canvas.create_text(396, 31, anchor="nw",text="Settings",fill="#ffffff",font=("Inter", 48 * -1))
        self.settingItems.append(pageTitle)


        t1 = self.canvas.create_text(396, 117, anchor="nw", text="Set path for account #1", fill="#ffffff", font=("Inter", 20 * -1))
        t2 = self.canvas.create_text(
            397,
            174,
            anchor="nw",
            text="Set path for account #2",
            fill="#ffffff",
            font=("Inter", 20 * -1)
        )
        t3 = self.canvas.create_text(
            397,
            232,
            anchor="nw",
            text="Set path for account #3",
            fill="#ffffff",
            font=("Inter", 20 * -1)
        )
        self.settingItems.extend([t1, t2, t3])

        self.browseButtonImg = tk.PhotoImage(file=self.load_asset("browse.png"))
        self.accountOneBtn = self.flatButton(image=self.browseButtonImg, command=lambda: self.setDir(1))
        self.accountOneBtn.place(x=742, y=108, width=152, height=41)
        self.settingButtons.append(self.accountOneBtn)

        self.accountTwoBtn = self.flatButton(image=self.browseButtonImg, command=lambda: self.setDir(2))
        self.accountTwoBtn.place(x=742, y=166, width=152, height=41)
        self.settingButtons.append(self.accountTwoBtn)

        self.accountThreeBtn = self.flatButton(image=self.browseButtonImg, command=lambda: self.setDir(3))
        self.accountThreeBtn.place(x=742, y=224, width=152, height=41)
        self.settingButtons.append(self.accountThreeBtn)

    def drawAccounts(self):
        print("Loading Accounts...")

    def drawAuto(self):
        print("Loading Automation...")

    # ------------------ Run ------------------
    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()
