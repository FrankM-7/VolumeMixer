import tkinter as tk
from tkinter import ttk
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
import serial
from PIL import Image
from pystray import MenuItem as item
import pystray
from threading import Thread

class CustomGUI:
    def __init__(self, root):
        processes = []
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name():
                processes.append(session.Process.name())

        self.root = root
        self.root.title("Custom GUI")
        self.root.protocol('WM_DELETE_WINDOW', self.withdraw_window)

        # Initialize variables for dropdown options
        self.options_1 = processes
        self.options_2 = processes
        self.options_3 = processes
        self.options_4 = processes

        # Create dropdowns
        self.dropdown_1 = ttk.Combobox(root, values=self.options_1)
        self.dropdown_2 = ttk.Combobox(root, values=self.options_2)
        self.dropdown_3 = ttk.Combobox(root, values=self.options_3)
        self.dropdown_4 = ttk.Combobox(root, values=self.options_4)

        # Create Refresh button
        self.refresh_button = tk.Button(root, text="Refresh", command=self.refresh_options)

        # Place widgets on the grid
        self.dropdown_1.grid(row=0, column=0, padx=10, pady=10)
        self.dropdown_2.grid(row=0, column=1, padx=10, pady=10)
        self.dropdown_3.grid(row=1, column=0, padx=10, pady=10)
        self.dropdown_4.grid(row=1, column=1, padx=10, pady=10)
        self.refresh_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Bind the function to the <<ComboboxSelected>> event for each dropdown
        self.dropdown_1.bind("<<ComboboxSelected>>", lambda event, dropdown=self.dropdown_1: self.on_dropdown_selected(event, dropdown))
        self.dropdown_2.bind("<<ComboboxSelected>>", lambda event, dropdown=self.dropdown_2: self.on_dropdown_selected(event, dropdown))
        self.dropdown_3.bind("<<ComboboxSelected>>", lambda event, dropdown=self.dropdown_3: self.on_dropdown_selected(event, dropdown))
        self.dropdown_4.bind("<<ComboboxSelected>>", lambda event, dropdown=self.dropdown_4: self.on_dropdown_selected(event, dropdown))

        # Serial Port Initialization
        self.serial_port = serial.Serial('COM6', 9600)

        # Periodically check for new data
        self.root.after(10, self.check_serial_data)

        self.processes = [None, None, None, None]

    def refresh_options(self):
        processesNames = []
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and session.Process.name():
                processesNames.append(session.Process.name())

        # You can update the options based on your requirements
        self.options_1 = processesNames
        self.options_2 = processesNames
        self.options_3 = processesNames
        self.options_4 = processesNames

        # Update the values of the dropdowns
        self.dropdown_1['values'] = self.options_1
        self.dropdown_2['values'] = self.options_2
        self.dropdown_3['values'] = self.options_3
        self.dropdown_4['values'] = self.options_4

    def on_dropdown_selected(self, event, dropdown):
        # Get the selected value when an option is selected
        selected_option = event.widget.get()
        print(f"Selected option: {selected_option} from dropdown: {dropdown}")
        index = -1
        if str(dropdown)[-1] == 'x':
            index = 0
        else:
            index = int(str(dropdown)[-1]) - 1

        for session in AudioUtilities.GetAllSessions():
            if session.Process and session.Process.name() == selected_option:
                self.processes[index] = session
                break

    def check_serial_data(self):
        # Check for new data from the serial port
        if self.serial_port.in_waiting > 0:
            serial_data = self.serial_port.readline().decode('utf-8').strip()

            # comes from pico
            encoderID = int(serial_data.split(' ')[0].strip()) - 1
            cmd = serial_data.split(' ')[1].strip()

            print(f"encoderID: {encoderID}, cmd: {cmd}")

            knob = None
            if encoderID == 0:
                knob = self.dropdown_1
            elif encoderID == 1:
                knob = self.dropdown_2
            elif encoderID == 2:
                knob = self.dropdown_3
            elif encoderID == 3:
                knob = self.dropdown_4

            print(f"knob: {knob.get()}")
            # if the knob doesn't have a process yet, find it
            if self.processes[encoderID] is None:
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    if session.Process and session.Process.name() == knob.get():
                        self.processes[encoderID] = session
                        break

            # if the knob has a process, change the volume
            if self.processes[encoderID] is not None:
                volume = self.processes[encoderID]._ctl.QueryInterface(ISimpleAudioVolume)
                if cmd == 'CW':
                    volume.SetMasterVolume(min(volume.GetMasterVolume() + 0.05, 1.0), None)
                elif cmd == 'CCW':
                    volume.SetMasterVolume(max(volume.GetMasterVolume() - 0.05, 0.0), None)
                print("volume.GetMasterVolume(): %s" % volume.GetMasterVolume())

        # Schedule the next check after 100 milliseconds
        self.root.after(10, self.check_serial_data)

    def withdraw_window(self):
        self.root.withdraw()
        image = Image.open("icon.png")
        menu = (item('Quit', self.quit_window), item('Show', self.show_window))
        icon = pystray.Icon("name", image, "title", menu)

        def run_icon():
            icon.run()

        icon_thread = Thread(target=run_icon)
        icon_thread.start()

    def quit_window(self, icon, item):
        icon.stop()
        self.root.destroy()

    def show_window(self, icon, item):
        icon.stop()
        self.root.after(0, self.root.deiconify)

if __name__ == "__main__":
    root = tk.Tk()
    app = CustomGUI(root)
    root.mainloop()
