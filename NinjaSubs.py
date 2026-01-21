""" - NINJASUBS Editor-
https://github.com/VincentNLOBJ/NinjaSubs

VincentNL 2026
❤️ [Ko-fi](https://ko-fi.com/vincentnl)
❤️ [Patreon](https://patreon.com/vincentnl) """

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
import struct, json, re
from pathlib import Path
import os
import sys


class njSubs_Editor:

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def __init__(self, root):
        self.root = root
        self.root.title("NinjaSubs")
        self.root.geometry("900x680")
        icon_path = self.resource_path("ninja.ico")
        self.root.iconbitmap(icon_path)
        self.root.resizable(False, False)
        self.scenes = {0: []}
        self.scene_names = {0: "None"}
        self.current_scene = 0
        self.project_loaded = False
        self.clipboard_data = None
        self.updating_fields = False
        self.asm_settings = {
            'game_binary': '', 'executable_base_offset': '0x8c010000',
            'empty_space_offset': '0x8C010000', 'empty_space_end': '0x00000000',
            'njprint_offset': '0x8C010000',
            'njprint_color_offset': '0x8C010000',
            'timer_offset': '0x8C010000', 'base_color_argb': 'ffbfbfbf',
            'game_fps': '60', 'backup_executable': True, 'ignore_font_fix': False
        }
        self._setup_ui()
        self.disable_all_controls()

    @property
    def subtitles(self):
        if self.current_scene not in self.scenes:
            self.scenes[self.current_scene] = []
        return self.scenes[self.current_scene]

    def disable_all_controls(self):
        self.scene_combo.config(state=tk.DISABLED)
        self.scene_name_entry.config(state=tk.DISABLED)
        self.add_sub_btn.config(state=tk.DISABLED)
        self.delete_sub_btn.config(state=tk.DISABLED)
        self.new_scene_btn.config(state=tk.DISABLED)
        self.delete_scene_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.export_asm_btn.config(state=tk.DISABLED)
        self.asm_settings_btn.config(state=tk.DISABLED)
        for widget in self.time_widgets.values():
            widget.config(state=tk.DISABLED)
        self.x_entry.config(state=tk.DISABLED)
        self.y_entry.config(state=tk.DISABLED)
        self.opacity_entry.config(state=tk.DISABLED)
        self.project_loaded = False

    def enable_all_controls(self):
        self.scene_combo.config(state='readonly')
        self.scene_name_entry.config(state=tk.NORMAL)
        self.add_sub_btn.config(state=tk.NORMAL)
        self.new_scene_btn.config(state=tk.NORMAL)
        self.delete_scene_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)
        self.export_asm_btn.config(state=tk.NORMAL)
        self.asm_settings_btn.config(state=tk.NORMAL)
        self.project_loaded = True

    def update_char_count(self, e=None):
        text = self.text_edit_widget.get("1.0", tk.END).rstrip('\n')
        byte_count = len(text.encode('utf-8'))
        self.char_count_label.config(text=f"{byte_count} bytes")

    def save_text_entry(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select an entry to save")
            return
        try:
            idx = int(sel[0])
            if idx >= len(self.subtitles):
                return
        except (ValueError, IndexError):
            return

        text = self.text_edit_widget.get("1.0", tk.END).rstrip('\n')

        # Validate each line doesn't exceed 36 bytes
        lines = text.split('\n')
        exceeded_lines = []
        for i, line in enumerate(lines, 1):
            if len(line.encode('utf-8')) > 36:
                exceeded_lines.append(f"Line {i}: {len(line.encode('utf-8'))} bytes")

        if exceeded_lines:
            msg = "The following lines exceed 36 bytes:\n" + "\n".join(exceeded_lines)
            messagebox.showerror("Error", msg)
            return

        # Save the text
        self.subtitles[idx]['text'] = text

        # Update x position based on auto-center setting
        if self.subtitles[idx].get('auto_center', True):
            first_line = lines[0] if lines else ""
            self.subtitles[idx]['x'] = self.calculate_centered_x(first_line)

        self.refresh_tree()
        self.tree.selection_set(str(idx))

    def _setup_ui(self):
        cf = ttk.Frame(self.root)
        cf.pack(fill=tk.X, padx=20, pady=10)
        ttk.Button(cf, text="New Project", command=self.new_project).pack(side=tk.LEFT, padx=5, ipady=5, ipadx=4)
        ttk.Button(cf, text="Load Project", command=self.load_file).pack(side=tk.LEFT, padx=5, ipady=5, ipadx=4)
        self.save_btn = ttk.Button(cf, text="Save Project", command=self.save_project)
        self.save_btn.pack(side=tk.LEFT, padx=5, ipady=5, ipadx=4)
        # Scene and Binary Frames Container
        top_container = ttk.Frame(self.root)
        top_container.pack(padx=25, pady=10, fill=tk.X)
        # Scene Frame on the left
        sf = ttk.LabelFrame(top_container, text="Select Scene", padding=10)
        sf.pack(side=tk.LEFT, expand=False, fill=tk.BOTH, pady=5)
        scene_frame = ttk.Frame(sf)
        scene_frame.pack(fill=tk.X, anchor=tk.W)
        ttk.Label(scene_frame, text="Scene:").pack(side=tk.LEFT, padx=5)
        self.scene_var = tk.StringVar(value="0")
        self.scene_combo = ttk.Combobox(scene_frame, textvariable=self.scene_var, width=5, state='readonly')
        self.scene_combo.pack(side=tk.LEFT, padx=5)
        self.scene_combo.bind("<<ComboboxSelected>>", self.on_scene_selected)
        ttk.Label(scene_frame, text="Name:").pack(side=tk.LEFT, padx=5)
        self.scene_name_var = tk.StringVar(value="")
        self.scene_name_entry = ttk.Entry(scene_frame, textvariable=self.scene_name_var, width=20)
        self.scene_name_entry.pack(side=tk.LEFT, padx=5)
        self.scene_name_var.trace('w', lambda *args: self.update_scene_name())
        self.new_scene_btn = ttk.Button(scene_frame, text="Add", command=self.new_scene)
        self.new_scene_btn.pack(side=tk.LEFT, padx=5, ipady=5)
        self.delete_scene_btn = ttk.Button(scene_frame, text="Delete", command=self.delete_scene)
        self.delete_scene_btn.pack(side=tk.LEFT, padx=5, ipady=5)
        self.update_scene_combo()
        # Binary Frame on the right
        bf = ttk.LabelFrame(top_container, text="Binary", padding=10)
        bf.pack(side=tk.LEFT, fill=tk.X, padx=(30, 0), pady=5)
        self.asm_settings_btn = ttk.Button(bf, text="ASM Settings", command=self.open_asm_settings)
        self.asm_settings_btn.pack(side=tk.LEFT, padx=5, ipady=5, ipadx=4)
        self.export_asm_btn = ttk.Button(bf, text="Patch Game Binary", command=self.save_output)
        self.export_asm_btn.pack(side=tk.LEFT, padx=5, ipady=5, ipadx=4)
        tf = ttk.Frame(self.root)
        tf.pack(fill=tk.X, expand=False, padx=(25, 10), pady=10)
        self.tree = ttk.Treeview(tf, columns=("Start", "End", "Text", "Bytes", "X", "Y", "Color", "Opacity"), height=8)
        for col, heading, width in [("#0", "Idx", 35), ("Start", "Start Time", 130),
                                    ("End", "End Time", 130), ("Text", "Text (First 36 chars)", 320),
                                    ("Bytes", "Size", 40), ("X", "X", 40), ("Y", "Y", 40), ("Color", "Color", 42),
                                    ("Opacity", "Opacity", 52)]:
            self.tree.heading(col, text=heading)
            if col == "Text":
                self.tree.column(col, width=width, stretch=True)
            else:
                self.tree.column(col, width=width, anchor=tk.CENTER)
        self.tree.grid(row=0, column=0, sticky='nsew')
        style = ttk.Style()
        style.layout('Vertical.TScrollbar', [('Vertical.Scrollbar.trough',
                                              {'children': [
                                                  ('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'})],
                                                  'sticky': 'ns'})])
        sb = ttk.Scrollbar(tf, orient=tk.VERTICAL, command=self.on_scroll, style='Vertical.TScrollbar')
        sb.grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscroll=sb.set)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<MouseWheel>", self.on_tree_scroll)
        self.tree.bind("<Button-4>", self.on_tree_scroll)
        self.tree.bind("<Button-5>", self.on_tree_scroll)
        self.tree.bind("<Button-3>", self.on_tree_right_click)
        self.tree.bind("<Up>", self.on_tree_scroll)
        self.tree.bind("<Down>", self.on_tree_scroll)
        self.tree.bind("<Prior>", self.on_tree_scroll)
        self.tree.bind("<Next>", self.on_tree_scroll)
        self.color_canvases = {}
        lb = ttk.Frame(self.root)
        lb.pack(fill=tk.X, padx=20, pady=(0, 5))
        self.add_sub_btn = ttk.Button(lb, text="Add Sub", command=self.add_entry)
        self.add_sub_btn.pack(side=tk.LEFT, padx=5, ipady=5)
        self.delete_sub_btn = ttk.Button(lb, text="Delete Sub", command=self.delete_entry)
        self.delete_sub_btn.pack(side=tk.LEFT, padx=5, ipady=5)
        ef = ttk.LabelFrame(self.root, text="Edit Selected Entry", padding=10)
        ef.pack(padx=25, pady=20, expand=False, fill=tk.X)
        main_container = ttk.Frame(ef)
        main_container.pack(fill=tk.BOTH, expand=True)
        start_frame = ttk.Frame(main_container)
        start_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(10, 20))
        ttk.Label(start_frame, text="Start Time:", font=("Arial", 10, "bold")).pack(anchor=tk.CENTER, pady=(0, 5))
        start_units = ttk.Frame(start_frame)
        start_units.pack(anchor=tk.CENTER)
        for i, unit in enumerate(["HH", "MM", "SS", "MMM"]):
            ttk.Label(start_units, text=unit, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
            if i < 3:
                ttk.Label(start_units, text=":", font=("Arial", 11)).pack(side=tk.LEFT, padx=1)
        start_time_inputs = ttk.Frame(start_frame)
        start_time_inputs.pack(anchor=tk.CENTER)
        self.time_widgets = {}
        for i, (unit, width) in enumerate([("HH", 4), ("MM", 4), ("SS", 4), ("MMM", 4)]):
            widget = tk.Entry(start_time_inputs, width=width, font=("Arial", 11), justify=tk.CENTER)
            widget.pack(side=tk.LEFT, padx=2)
            for event in ["<MouseWheel>", "<Button-4>", "<Button-5>"]:
                widget.bind(event, lambda e, f=f"start_{unit.lower()}": self.scroll_time(e, f))
            self.time_widgets[f"start_{unit.lower()}"] = widget
            if i < 3:
                ttk.Label(start_time_inputs, text=":").pack(side=tk.LEFT, padx=1)
        end_frame = ttk.Frame(main_container)
        end_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 20))
        ttk.Label(end_frame, text="End Time:", font=("Arial", 10, "bold")).pack(anchor=tk.CENTER, pady=(0, 5))
        end_units = ttk.Frame(end_frame)
        end_units.pack(anchor=tk.CENTER)
        for i, unit in enumerate(["HH", "MM", "SS", "MMM"]):
            ttk.Label(end_units, text=unit, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
            if i < 3:
                ttk.Label(end_units, text=":", font=("Arial", 11)).pack(side=tk.LEFT, padx=1)
        end_time_inputs = ttk.Frame(end_frame)
        end_time_inputs.pack(anchor=tk.CENTER)
        for i, (unit, width) in enumerate([("HH", 4), ("MM", 4), ("SS", 4), ("MMM", 4)]):
            widget = tk.Entry(end_time_inputs, width=width, font=("Arial", 11), justify=tk.CENTER)
            widget.pack(side=tk.LEFT, padx=2)
            for event in ["<MouseWheel>", "<Button-4>", "<Button-5>"]:
                widget.bind(event, lambda e, f=f"end_{unit.lower()}": self.scroll_time(e, f))
            self.time_widgets[f"end_{unit.lower()}"] = widget
            if i < 3:
                ttk.Label(end_time_inputs, text=":").pack(side=tk.LEFT, padx=1)
        ttk.Separator(main_container, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        position_frame = ttk.Frame(main_container)
        position_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        ttk.Label(position_frame, text="Position:", font=("Arial", 10, "bold")).pack(anchor=tk.CENTER, pady=(0, 5))
        x_frame = ttk.Frame(position_frame)
        x_frame.pack(fill=tk.X, pady=(0, 10))
        x_label_frame = ttk.Frame(x_frame)
        x_label_frame.pack(fill=tk.X)
        ttk.Label(x_label_frame, text="X Offset:", font=("Arial", 10)).pack(side=tk.LEFT, padx=2)
        self.x_var = tk.StringVar(value="2")
        self.x_entry = tk.Entry(x_label_frame, textvariable=self.x_var, width=4, font=("Arial", 11), justify=tk.CENTER)
        self.x_entry.pack(side=tk.LEFT, padx=2)
        self.x_trace_id = self.x_var.trace('w', lambda *args: self.auto_update_list())
        self.auto_center_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(x_label_frame, text="Auto-Center", variable=self.auto_center_var,
                        command=self.on_auto_center_toggle).pack(side=tk.LEFT, padx=10)
        y_frame = ttk.Frame(position_frame)
        y_frame.pack(fill=tk.X)
        ttk.Label(y_frame, text="Y Offset:", font=("Arial", 10)).pack(side=tk.LEFT, padx=2)
        self.y_var = tk.StringVar(value="25")
        self.y_entry = tk.Entry(y_frame, textvariable=self.y_var, width=4, font=("Arial", 11), justify=tk.CENTER)
        self.y_entry.pack(side=tk.LEFT, padx=2)
        self.y_trace_id = self.y_var.trace('w', lambda *args: self.auto_update_list())
        ttk.Separator(main_container, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        color_section_frame = ttk.Frame(main_container)
        color_section_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        ttk.Label(color_section_frame, text="Color:", font=("Arial", 10, "bold")).pack(anchor=tk.CENTER, pady=(0, 5))
        color_frame = ttk.Frame(color_section_frame)
        color_frame.pack(pady=(0, 10), padx=(0, 20), anchor=tk.W)
        ttk.Label(color_frame, text="Color:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 16))
        self.color_var = tk.StringVar(value="ffbfbfbf")
        self.color_canvas = tk.Canvas(color_frame, width=35, height=25, bg=self._hex_to_display("ffbfbfbf"),
                                      relief=tk.SUNKEN, bd=0, cursor="hand2")
        self.color_canvas.pack(side=tk.LEFT, padx=2)
        self.color_canvas.bind("<Button-1>", self.pick_subtitle_color)
        opacity_frame = ttk.Frame(color_section_frame)
        opacity_frame.pack(fill=tk.X, anchor=tk.W)
        ttk.Label(opacity_frame, text="Opacity:", font=("Arial", 10)).pack(side=tk.LEFT, padx=2)
        self.opacity_var = tk.StringVar(value="255")
        self.opacity_entry = tk.Entry(opacity_frame, textvariable=self.opacity_var, width=4, font=("Arial", 11),
                                      justify=tk.CENTER)
        self.opacity_entry.pack(side=tk.LEFT, padx=2)
        self.opacity_trace_id = self.opacity_var.trace('w', lambda *args: self.auto_update_list())

        text_section = ttk.Frame(ef)
        text_section.pack(fill=tk.X, padx=10, pady=(5, 0))
        text_label_frame = ttk.Frame(text_section)
        text_label_frame.pack(pady=(0, 5), padx=195, anchor=tk.W)
        ttk.Label(text_label_frame, text="Text:", font=("Arial", 10, "bold")).pack()
        text_and_button_frame = ttk.Frame(text_section)
        text_and_button_frame.pack(anchor=tk.W, pady=(0, 5))
        self.text_edit_widget = tk.Text(text_and_button_frame, font=("Arial", 11), height=6, wrap=tk.WORD, width=50,
                                        padx=5, pady=5, bg="#f0f0f0", fg="black")
        self.text_edit_widget.pack(side=tk.LEFT)

        self.save_entry_btn = ttk.Button(text_and_button_frame, text="Save Entry", command=self.save_text_entry)
        self.save_entry_btn.pack(side=tk.LEFT, padx=(20, 0), ipady=5)
        char_count_frame = ttk.Frame(text_section)
        char_count_frame.pack(fill=tk.X, pady=(10, 0))
        self.char_count_label = ttk.Label(char_count_frame, text="0 bytes", font=("Arial", 9, "bold"))
        self.char_count_label.pack(side=tk.LEFT)
        self.text_edit_widget.bind("<KeyRelease>", self.update_char_count)
        self.root.after(100, self._bind_time_updates)
        # Initialize with empty/disabled state
        self.root.after(150, self.clear_edit_fields)

    def _bind_time_updates(self):
        for key, widget in self.time_widgets.items():
            widget.bind("<Return>", lambda e: self.auto_update_list())

    def _hex_to_display(self, argb_hex):
        try:
            val = int(argb_hex, 16)
            r = (val >> 16) & 0xFF
            g = (val >> 8) & 0xFF
            b = (val >> 0) & 0xFF
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#bfbfbf"

    def argb_to_rgb(self, argb_hex):
        try:
            val = int(argb_hex, 16)
            r = (val >> 16) & 0xFF
            g = (val >> 8) & 0xFF
            b = (val >> 0) & 0xFF
            return (r, g, b)
        except:
            return (191, 191, 191)

    def rgb_to_argb(self, r, g, b, a=255):
        val = (a << 24) | (r << 16) | (g << 8) | (b << 0)
        return f"{val:08x}"

    def extract_alpha_from_argb(self, argb_hex):
        try:
            val = int(argb_hex, 16)
            a = (val >> 24) & 0xFF
            return a
        except:
            return 255

    def pick_subtitle_color(self, e=None):
        rgb, _ = colorchooser.askcolor(self.argb_to_rgb(self.color_var.get()), title="Pick Subtitle Color")
        if rgb:
            r, g, b = [int(c) for c in rgb]
            opacity = int(self.opacity_var.get() or 255)
            self.color_var.set(self.rgb_to_argb(r, g, b, opacity))
            self.color_canvas.config(bg=self._hex_to_display(self.color_var.get()))
            self.auto_update_list()

    def ms_to_components(self, ms):
        return ms // 3600000, (ms % 3600000) // 60000, (ms % 60000) // 1000, ms % 1000

    def ms_to_timecode_display(self, ms):
        h, m, s, mmm = self.ms_to_components(ms)
        return f"{h:02d}:{m:02d}:{s:02d}:{mmm:03d}"

    def components_to_ms(self, h, m, s, ms):
        return h * 3600000 + m * 60000 + s * 1000 + ms

    def update_scene_combo(self):
        scenes = sorted(self.scenes.keys())
        self.scene_combo['values'] = [str(s + 1) for s in scenes]
        if str(self.current_scene) not in [str(s) for s in scenes]:
            if scenes:
                self.current_scene = scenes[0]
        self.scene_var.set(str(self.current_scene + 1))
        self.scene_name_var.set(self.scene_names.get(self.current_scene, ""))

    def update_scene_name(self):
        self.scene_names[self.current_scene] = self.scene_name_var.get()

    def on_scene_selected(self, e=None):
        self.current_scene = int(self.scene_var.get()) - 1
        self.scene_name_var.set(self.scene_names.get(self.current_scene, ""))
        self.clear_edit_fields()
        self.refresh_tree()
        # Auto-select first entry if available
        if self.subtitles:
            self.tree.selection_set("0")
            self.on_select()

    def new_scene(self):
        if self.scenes:
            new_num = max(self.scenes.keys()) + 1
        else:
            new_num = 0
        self.scenes[new_num] = []
        self.scene_names[new_num] = "None"
        self.update_scene_combo()
        self.current_scene = new_num
        self.scene_var.set(str(new_num + 1))
        self.scene_name_var.set("None")
        self.clear_edit_fields()
        self.refresh_tree()

    def delete_scene(self):
        if len(self.scenes) <= 1:
            messagebox.showwarning("Warning", "Cannot delete the last scene")
            return
        if messagebox.askyesno("Confirm", f"Delete scene {self.current_scene}?"):
            deleted_scene = self.current_scene
            del self.scenes[self.current_scene]
            del self.scene_names[self.current_scene]
            self.update_scene_combo()

            # Select previous scene if available
            available_scenes = sorted(self.scenes.keys())
            if available_scenes:
                # Find the scene that was before the deleted one
                prev_scene = None
                for scene_num in available_scenes:
                    if scene_num < deleted_scene:
                        prev_scene = scene_num
                    else:
                        break

                # If no previous scene, select the first available
                if prev_scene is None:
                    prev_scene = available_scenes[0]

                self.current_scene = prev_scene
                self.scene_var.set(str(prev_scene + 1))
                self.scene_name_var.set(self.scene_names.get(prev_scene, ""))
                self.clear_edit_fields()
                self.refresh_tree()

                # Auto-select first entry of the selected scene if available
                if self.subtitles:
                    self.tree.selection_set("0")
                    self.on_select()

    def refresh_tree(self):
        existing_items = list(self.tree.get_children())
        for item in existing_items:
            self.tree.delete(item)

        for i, sub in enumerate(self.subtitles):
            bs = len(sub['text'].encode('utf-8'))
            auto_center = sub.get('auto_center', True)
            x = "-" if auto_center else sub.get('x', 0)
            y = sub.get('y', 0)
            color = sub.get('color', 'ffbfbfbf')
            opacity = sub.get('opacity', 255)
            text_display = sub['text']
            if '\n' in text_display:
                first_line = text_display.split('\n')[0]
                text_display = first_line + " [...]"
            values = (self.ms_to_timecode_display(sub['start']),
                      self.ms_to_timecode_display(sub['end']),
                      text_display[:40], f"{bs}", x, y, "", opacity)
            self.tree.insert("", tk.END, iid=str(i), text=str(i + 1), values=values)

        self.root.after(10, self.create_color_squares)

    def create_color_squares(self):
        visible_items = set(self.tree.get_children())

        for i in range(len(self.subtitles)):
            if str(i) not in visible_items:
                if str(i) in self.color_canvases:
                    self.color_canvases[str(i)].destroy()
                    del self.color_canvases[str(i)]
                continue

            sub = self.subtitles[i]
            color = sub.get('color', 'ffbfbfbf')
            bbox = self.tree.bbox(str(i), "Color")
            if bbox:
                x, y, w, h = bbox
                size = min(h - 4, 20)
                pos_x = x + (w - size) // 2
                pos_y = y + (h - size) // 2

                if str(i) not in self.color_canvases:
                    canvas = tk.Canvas(self.tree, width=size, height=size, bg=self._hex_to_display(color),
                                       relief=tk.SUNKEN, bd=0, cursor="hand2", highlightthickness=0)
                    self.color_canvases[str(i)] = canvas
                    canvas.bind("<Button-1>", lambda e, idx=i: self.on_color_click(idx))
                    canvas.place(x=pos_x, y=pos_y, width=size, height=size)
                else:
                    canvas = self.color_canvases[str(i)]
                    canvas.config(bg=self._hex_to_display(color), width=size, height=size)
                    canvas.place(x=pos_x, y=pos_y, width=size, height=size)

        for canvas_id in list(self.color_canvases.keys()):
            if int(canvas_id) >= len(self.subtitles):
                self.color_canvases[canvas_id].destroy()
                del self.color_canvases[canvas_id]

    def on_scroll(self, *args):
        self.tree.yview(*args)
        self.root.after(5, self.create_color_squares)

    def on_tree_scroll(self, e=None):
        self.root.after(5, self.create_color_squares)

    def on_tree_right_click(self, e):
        item = self.tree.identify('item', e.x, e.y)
        if item and item not in self.tree.selection():
            self.tree.selection_set(item)

        menu = tk.Menu(self.root, tearoff=False)

        copy_menu = tk.Menu(menu, tearoff=False)
        copy_menu.add_command(label="Text", command=lambda: self.copy_property('text'))
        copy_menu.add_command(label="Color", command=lambda: self.copy_property('color'))
        copy_menu.add_command(label="X", command=lambda: self.copy_property('x'))
        copy_menu.add_command(label="Y", command=lambda: self.copy_property('y'))
        copy_menu.add_command(label="Opacity", command=lambda: self.copy_property('opacity'))
        menu.add_cascade(label="Copy", menu=copy_menu)

        paste_menu = tk.Menu(menu, tearoff=False)
        paste_menu.add_command(label="Text", command=lambda: self.paste_property('text'))
        paste_menu.add_command(label="Color", command=lambda: self.paste_property('color'))
        paste_menu.add_command(label="X", command=lambda: self.paste_property('x'))
        paste_menu.add_command(label="Y", command=lambda: self.paste_property('y'))
        paste_menu.add_command(label="Opacity", command=lambda: self.paste_property('opacity'))
        menu.add_cascade(label="Paste", menu=paste_menu)

        menu.add_separator()
        menu.add_command(label="Import .srt", command=self.import_srt)

        menu.post(e.x_root, e.y_root)

    def copy_property(self, prop):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx >= len(self.subtitles):
            return
        sub = self.subtitles[idx]
        if self.clipboard_data is None:
            self.clipboard_data = {}
        if prop == 'text':
            self.clipboard_data['text'] = sub['text']
        elif prop == 'color':
            self.clipboard_data['color'] = sub.get('color', 'ffbfbfbf')
        elif prop == 'x':
            self.clipboard_data['x'] = sub.get('x', 0)
        elif prop == 'y':
            self.clipboard_data['y'] = sub.get('y', 0)
        elif prop == 'opacity':
            self.clipboard_data['opacity'] = sub.get('opacity', 255)

    def paste_property(self, prop):
        if self.clipboard_data is None or prop not in self.clipboard_data:
            return
        sel = self.tree.selection()
        if not sel:
            return

        selected_items = list(sel)
        for item in selected_items:
            try:
                idx = int(item)
                if idx >= len(self.subtitles):
                    continue
                sub = self.subtitles[idx]
                if prop == 'text':
                    sub['text'] = self.clipboard_data['text']
                elif prop == 'color':
                    sub['color'] = self.clipboard_data['color']
                elif prop == 'x':
                    sub['x'] = self.clipboard_data['x']
                    sub['auto_center'] = False
                elif prop == 'y':
                    sub['y'] = self.clipboard_data['y']
                elif prop == 'opacity':
                    sub['opacity'] = self.clipboard_data['opacity']
            except (ValueError, IndexError):
                continue

        self.refresh_tree()
        # Reselect the previously selected items
        for item in selected_items:
            self.tree.selection_add(item)

    def import_srt(self):
        fp = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt"), ("All files", "*.*")])
        if not fp:
            return

        if not messagebox.askyesno("Confirm", "Do you want to overwrite the current scene?"):
            return

        try:
            srt_subs = self.parse_srt(fp)
            if not srt_subs:
                messagebox.showwarning("Warning", "No subtitles found in SRT file")
                return

            self.subtitles.clear()
            for srt_sub in srt_subs:
                text = srt_sub['text'][:]
                sub = {
                    'start': srt_sub['start'],
                    'end': srt_sub['end'],
                    'text': text,
                    'x': 2,
                    'y': 25,
                    'color': 'ffbfbfbf',
                    'opacity': 255,
                    'auto_center': True
                }
                self.subtitles.append(sub)

            self.subtitles.sort(key=lambda x: x['start'])
            self.refresh_tree()
            # Auto-select first entry after import
            if self.subtitles:
                self.tree.selection_set("0")
                self.on_select()
            messagebox.showinfo("Success", f"Imported {len(srt_subs)} subtitles from SRT file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import SRT file: {e}")

    def parse_srt(self, filepath):
        srt_subs = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            blocks = content.split('\n\n')

            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue

                timecode_line = lines[1]
                timecode_match = re.match(
                    r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                    timecode_line)
                if not timecode_match:
                    continue

                h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, timecode_match.groups())
                start = self.components_to_ms(h1, m1, s1, ms1)
                end = self.components_to_ms(h2, m2, s2, ms2)

                text = '\n'.join(lines[2:]).strip()

                srt_subs.append({
                    'start': start,
                    'end': end,
                    'text': text
                })

            return srt_subs
        except Exception as e:
            print(f"SRT Parse error: {e}")
            return []

    def on_select(self, e=None):
        sel = self.tree.selection()
        if not sel:
            self.clear_edit_fields()
            return
        try:
            display_idx = int(sel[0])
            idx = display_idx
            if idx >= len(self.subtitles):
                self.clear_edit_fields()
                return
            sub = self.subtitles[idx]
        except (ValueError, IndexError):
            self.clear_edit_fields()
            return

        self.updating_fields = True

        if hasattr(self, 'x_trace_id'):
            self.x_var.trace_remove('write', self.x_trace_id)
        if hasattr(self, 'y_trace_id'):
            self.y_var.trace_remove('write', self.y_trace_id)
        if hasattr(self, 'opacity_trace_id'):
            self.opacity_var.trace_remove('write', self.opacity_trace_id)

        # Enable all time widgets
        for widget in self.time_widgets.values():
            widget.config(state=tk.NORMAL)

        h, m, s, ms = self.ms_to_components(sub['start'])
        for u, v in [('hh', h), ('mm', m), ('ss', s), ('mmm', ms)]:
            fmt = f"{v:03d}" if u == "mmm" else f"{v:02d}"
            self.time_widgets[f"start_{u}"].delete(0, tk.END)
            self.time_widgets[f"start_{u}"].insert(0, fmt)
        h, m, s, ms = self.ms_to_components(sub['end'])
        for u, v in [('hh', h), ('mm', m), ('ss', s), ('mmm', ms)]:
            fmt = f"{v:03d}" if u == "mmm" else f"{v:02d}"
            self.time_widgets[f"end_{u}"].delete(0, tk.END)
            self.time_widgets[f"end_{u}"].insert(0, fmt)
        auto_center = sub.get('auto_center', True)
        self.auto_center_var.set(auto_center)
        if auto_center:
            self.x_entry.config(state=tk.DISABLED)
            self.x_var.set("-")
        else:
            self.x_entry.config(state=tk.NORMAL)
            self.x_var.set(str(sub.get('x', 0)))
        self.y_entry.config(state=tk.NORMAL)
        self.y_var.set(str(sub.get('y', 0)))
        color = sub.get('color', 'ffbfbfbf')
        opacity = sub.get('opacity', 255)
        self.color_var.set(color)
        self.opacity_var.set(str(opacity))
        self.opacity_entry.config(state=tk.NORMAL)
        self.color_canvas.config(bg=self._hex_to_display(color))

        self.text_edit_widget.config(state=tk.NORMAL, bg="white", fg="black")
        self.text_edit_widget.delete("1.0", tk.END)
        self.text_edit_widget.insert("1.0", sub['text'])
        self.save_entry_btn.config(state=tk.NORMAL)
        self.delete_sub_btn.config(state=tk.NORMAL)
        self.update_char_count()

        self.x_trace_id = self.x_var.trace('w', lambda *args: self.auto_update_list())
        self.y_trace_id = self.y_var.trace('w', lambda *args: self.auto_update_list())
        self.opacity_trace_id = self.opacity_var.trace('w', lambda *args: self.auto_update_list())

        self.updating_fields = False

    def on_auto_center_toggle(self):
        self.x_entry.config(state=tk.DISABLED if self.auto_center_var.get() else tk.NORMAL)
        self.auto_update_list()

    def calculate_centered_x(self, text):
        text_len = len(text.encode('utf-8'))
        return ((36 - text_len) // 2) + 2

    def clear_edit_fields(self):
        self.updating_fields = True
        for w in self.time_widgets.values():
            w.config(state=tk.NORMAL)
            w.delete(0, tk.END)
            w.config(state=tk.DISABLED)
        self.x_var.set("0")
        self.y_var.set("0")
        self.auto_center_var.set(True)
        self.x_entry.config(state=tk.DISABLED)
        self.y_entry.config(state=tk.DISABLED)
        self.color_var.set("ffbfbfbf")
        self.opacity_var.set("255")
        self.opacity_entry.config(state=tk.DISABLED)
        self.color_canvas.config(bg=self._hex_to_display("ffbfbfbf"))
        self.text_edit_widget.config(state=tk.NORMAL, bg="#f0f0f0", fg="#888888")
        self.text_edit_widget.delete("1.0", tk.END)
        self.text_edit_widget.config(state=tk.DISABLED)
        self.save_entry_btn.config(state=tk.DISABLED)
        self.delete_sub_btn.config(state=tk.DISABLED)
        self.update_char_count()
        self.updating_fields = False

    def auto_update_list(self, e=None):
        if self.updating_fields:
            return

        sel = self.tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
        except (IndexError, ValueError):
            return

        if idx >= len(self.subtitles):
            return

        try:
            sh = int(self.time_widgets['start_hh'].get() or 0)
            sm = int(self.time_widgets['start_mm'].get() or 0)
            ss = int(self.time_widgets['start_ss'].get() or 0)
            sms = int(self.time_widgets['start_mmm'].get() or 0)
            eh = int(self.time_widgets['end_hh'].get() or 0)
            em = int(self.time_widgets['end_mm'].get() or 0)
            es = int(self.time_widgets['end_ss'].get() or 0)
            ems = int(self.time_widgets['end_mmm'].get() or 0)
            start = self.components_to_ms(sh, sm, ss, sms)
            end = self.components_to_ms(eh, em, es, ems)
            auto_center = self.auto_center_var.get()
            text = self.subtitles[idx]['text']
            if auto_center:
                x = self.calculate_centered_x(text)
            else:
                x_str = self.x_var.get()
                x = int(x_str) if x_str and x_str != "-" else 0
            y = int(self.y_var.get() or 0)

            color_hex = self.color_var.get()
            opacity = int(self.opacity_var.get() or 255)
            opacity = max(0, min(255, opacity))

            r, g, b = self.argb_to_rgb(color_hex)
            color = self.rgb_to_argb(r, g, b, opacity)

            if start < end:
                sub_ref = self.subtitles[idx]
                sub_ref.update(
                    {'start': start, 'end': end, 'x': x, 'y': y, 'color': color, 'opacity': opacity,
                     'auto_center': auto_center})
                self.subtitles.sort(key=lambda x: x['start'])
                new_idx = self.subtitles.index(sub_ref)
                self.refresh_tree()
                self.tree.selection_set(str(new_idx))
        except (ValueError, IndexError):
            pass

    def scroll_time(self, e, field):
        delta = -1 if (e.num == 5 or e.delta < 0) else 1
        is_start = 'start' in field
        unit = field.split('_')[1]
        h = int((self.time_widgets['start_hh'] if is_start else self.time_widgets['end_hh']).get() or 0)
        m = int((self.time_widgets['start_mm'] if is_start else self.time_widgets['end_mm']).get() or 0)
        s = int((self.time_widgets['start_ss'] if is_start else self.time_widgets['end_ss']).get() or 0)
        ms = int((self.time_widgets['start_mmm'] if is_start else self.time_widgets['end_mmm']).get() or 0)
        total = self.components_to_ms(h, m, s, ms) + delta * {'mmm': 1, 'ss': 1000, 'mm': 60000, 'hh': 3600000}[unit]
        h, m, s, ms = self.ms_to_components(max(0, total))
        prefix = 'start' if is_start else 'end'
        for u, v, fmt in [('hh', h, '02d'), ('mm', m, '02d'), ('ss', s, '02d'), ('mmm', ms, '03d')]:
            self.time_widgets[f"{prefix}_{u}"].delete(0, tk.END)
            self.time_widgets[f"{prefix}_{u}"].insert(0, f"{v:{fmt}}")
        self.auto_update_list()
        return "break"

    def on_color_click(self, idx):
        if idx < len(self.subtitles):
            self.tree.selection_set(str(idx))
            self.on_select()
            rgb, _ = colorchooser.askcolor(self.argb_to_rgb(self.subtitles[idx]['color']),
                                           title="Pick Subtitle Color")
            if rgb:
                r, g, b = [int(c) for c in rgb]
                opacity = self.subtitles[idx].get('opacity', 255)
                self.subtitles[idx]['color'] = self.rgb_to_argb(r, g, b, opacity)
                self.color_var.set(self.subtitles[idx]['color'])
                self.color_canvas.config(bg=self._hex_to_display(self.subtitles[idx]['color']))
                if str(idx) in self.color_canvases:
                    self.color_canvases[str(idx)].config(bg=self._hex_to_display(self.subtitles[idx]['color']))
                self.refresh_tree()
                self.tree.selection_set(str(idx))

    def on_text_edit(self, e):
        sel = self.tree.selection()
        if not sel or self.tree.identify_column(e.x) != "#3":
            return
        idx = int(sel[0])
        self.cancel_text_edit()

        self.edit_entry = tk.Text(self.root, font=("Arial", 10), height=4, wrap=tk.WORD)
        self.edit_entry.insert("1.0", self.subtitles[idx]['text'])

        bbox = self.tree.bbox(sel[0], "#3")
        if bbox:
            screen_x = self.tree.winfo_rootx() + bbox[0]
            screen_y = self.tree.winfo_rooty() + bbox[1]
            root_x = screen_x - self.root.winfo_rootx()
            root_y = screen_y - self.root.winfo_rooty()
            self.edit_entry.place(x=root_x, y=root_y, width=bbox[2], height=100)
            self.edit_entry.focus()
            self.edit_entry.tag_add(tk.SEL, "1.0", tk.END)
            self.edit_idx = idx

            self.edit_entry.bind("<Control-Return>", self.save_text_edit)
            self.edit_entry.bind("<FocusOut>", self.save_text_edit)
            self.edit_entry.bind("<Escape>", self.cancel_text_edit)

    def save_text_edit(self, e=None):
        if not hasattr(self, 'edit_entry'):
            return

        text = self.edit_entry.get("1.0", tk.END).rstrip('\n')
        lines = text.split('\n')

        exceeded_lines = []
        for i, line in enumerate(lines, 1):
            if len(line.encode('utf-8')) > 36:
                exceeded_lines.append(f"Line {i}: {len(line.encode('utf-8'))} bytes")

        if exceeded_lines:
            msg = "The following lines exceed 36 bytes:\n" + "\n".join(exceeded_lines)
            messagebox.showerror("Error", msg)
            return

        self.subtitles[self.edit_idx]['text'] = text

        if self.subtitles[self.edit_idx].get('auto_center', True):
            first_line = lines[0] if lines else ""
            self.subtitles[self.edit_idx]['x'] = self.calculate_centered_x(first_line)

        self.refresh_tree()
        self.edit_entry.place_forget()

    def cancel_text_edit(self, e=None):
        if hasattr(self, 'edit_entry'):
            self.edit_entry.place_forget()

    def add_entry(self):
        if self.subtitles:
            s = self.subtitles[-1]['end']
            last_color = self.subtitles[-1].get('color', 'ffbfbfbf')
            last_opacity = self.subtitles[-1].get('opacity', 255)
            last_auto_center = self.subtitles[-1].get('auto_center', True)
            last_x = self.subtitles[-1].get('x', 0)
            last_y = self.subtitles[-1].get('y', 0)
            self.subtitles.append({'start': s, 'end': s + 1000, 'text': '', 'x': last_x, 'y': last_y,
                                   'color': last_color, 'opacity': last_opacity, 'auto_center': last_auto_center})
        else:
            self.subtitles.append({'start': 0, 'end': 1000, 'text': '', 'x': 0, 'y': 0,
                                   'color': 'ffbfbfbf', 'opacity': 255, 'auto_center': True})
        self.refresh_tree()
        # Auto-select the newly added entry
        new_idx = len(self.subtitles) - 1
        self.tree.selection_set(str(new_idx))
        self.on_select()

    def delete_entry(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select an entry to delete")
            return
        deleted_idx = int(sel[0])
        del self.subtitles[deleted_idx]
        self.subtitles.sort(key=lambda x: x['start'])
        self.refresh_tree()
        # Auto-select previous entry if available
        if self.subtitles:
            # If deleted the last entry, select the new last entry
            # Otherwise select the entry at the same index (which is now the next one)
            new_idx = min(deleted_idx, len(self.subtitles) - 1)
            self.tree.selection_set(str(new_idx))
            self.on_select()
        else:
            self.clear_edit_fields()

    def open_asm_settings(self):
        def pick_asm_color():
            rgb, _ = colorchooser.askcolor(self.argb_to_rgb(var_color.get()), title="Pick Base Color")
            if rgb:
                r, g, b = [int(c) for c in rgb]
                opacity = self.extract_alpha_from_argb(var_color.get())
                var_color.set(self.rgb_to_argb(r, g, b, opacity))
                self.settings_color_canvas.config(bg=self._hex_to_display(var_color.get()))

        w = tk.Toplevel(self.root)
        w.title("ASM Settings")
        w.geometry("600x500")
        icon_path = self.resource_path("ninja.ico")
        w.iconbitmap(icon_path)
        w.resizable(False, False)
        w.transient(self.root)
        w.grab_set()
        mf = ttk.Frame(w, padding=20)
        mf.pack(fill=tk.BOTH, expand=True)

        ttk.Label(mf, text="Game Binary:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=10)
        var_binary = tk.StringVar(value=self.asm_settings['game_binary'])
        gf = ttk.Frame(mf)
        gf.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=10)
        tk.Entry(gf, textvariable=var_binary, width=40, font=("Arial", 11)).pack(side=tk.LEFT, fill=tk.X, expand=True,
                                                                                 padx=(0, 5))
        ttk.Button(gf, text="Browse", command=lambda v=var_binary: self._browse_and_scan(v), width=10).pack(
            side=tk.LEFT, ipady=5)

        frames_container = ttk.Frame(mf)
        frames_container.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=20)

        njf = ttk.LabelFrame(frames_container, text="njPrint Offset", padding=15, relief=tk.SOLID, borderwidth=2)
        njf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        nj_fields = [('executable_base_offset', "Base Offset"), ('njprint_offset', "njPrint"),
                     ('njprint_color_offset', "njPrintColor")]
        vars_dict = {'game_binary': var_binary}
        for i, (key, label) in enumerate(nj_fields):
            ttk.Label(njf, text=label + ":").grid(row=i, column=0, sticky=tk.W, pady=8)
            var = tk.StringVar(value=self.asm_settings[key])
            vars_dict[key] = var
            tk.Entry(njf, textvariable=var, width=11, font=("Arial", 12)).grid(row=i, column=1, sticky=tk.EW, pady=8)
        njf.columnconfigure(1, weight=1)

        csf = ttk.LabelFrame(frames_container, text="Game Settings", padding=15, relief=tk.SOLID, borderwidth=2)
        csf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        ttk.Label(csf, text="Empty Space:").grid(row=0, column=0, sticky=tk.W, pady=8)
        empty_space_frame = ttk.Frame(csf)
        empty_space_frame.grid(row=0, column=1, sticky=tk.EW, pady=8)
        var_empty_start = tk.StringVar(value=self.asm_settings.get('empty_space_offset', '0x8C010000'))
        tk.Entry(empty_space_frame, textvariable=var_empty_start, width=12, font=("Arial", 11)).pack(side=tk.LEFT,
                                                                                                     padx=(0, 5))
        ttk.Label(empty_space_frame, text="to:").pack(side=tk.LEFT, padx=0)
        var_empty_end = tk.StringVar(value=self.asm_settings.get('empty_space_end', '0x00000000'))
        tk.Entry(empty_space_frame, textvariable=var_empty_end, width=12, font=("Arial", 11)).pack(side=tk.LEFT,
                                                                                                   padx=(5, 0))
        vars_dict['empty_space_offset'] = var_empty_start
        vars_dict['empty_space_end'] = var_empty_end

        ttk.Label(csf, text="Timer Offset:").grid(row=1, column=0, sticky=tk.W, pady=8)
        var_timer = tk.StringVar(value=self.asm_settings.get('timer_offset', '0x8C010000'))
        vars_dict['timer_offset'] = var_timer
        tk.Entry(csf, textvariable=var_timer, width=12, font=("Arial", 11)).grid(row=1, column=1, sticky=tk.W, pady=8)

        ttk.Label(csf, text="Game FPS:").grid(row=2, column=0, sticky=tk.W, pady=8)
        var_fps = tk.StringVar(value=self.asm_settings.get('game_fps', '60'))
        vars_dict['game_fps'] = var_fps
        tk.Entry(csf, textvariable=var_fps, width=5, font=("Arial", 12)).grid(row=2, column=1, sticky=tk.W, pady=8)

        color_backup_container = ttk.Frame(mf)
        color_backup_container.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=5)

        bcf = ttk.LabelFrame(color_backup_container, text="Default Color", padding=14, relief=tk.SOLID, borderwidth=2)
        bcf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        color_frame = ttk.Frame(bcf)
        color_frame.pack()

        var_color = tk.StringVar(value=self.asm_settings.get('base_color_argb', 'ffbfbfbf'))
        vars_dict['base_color_argb'] = var_color
        self.settings_color_canvas = tk.Canvas(color_frame, width=30, height=30, bg=self._hex_to_display(
            self.asm_settings.get('base_color_argb', 'ffbfbfbf')), relief=tk.SUNKEN, bd=1, cursor="hand2")
        self.settings_color_canvas.pack(side=tk.LEFT, padx=5)
        self.settings_color_canvas.bind("<Button-1>", lambda e: pick_asm_color())

        ttk.Label(color_frame, text="Opacity:").pack(side=tk.LEFT, padx=(20, 5))
        base_opacity = self.extract_alpha_from_argb(self.asm_settings.get('base_color_argb', 'ffbfbfbf'))
        var_opacity = tk.StringVar(value=str(base_opacity))
        vars_dict['base_opacity'] = var_opacity
        tk.Entry(color_frame, textvariable=var_opacity, width=6, font=("Arial", 11)).pack(side=tk.LEFT, padx=5)

        # Backup Executable option
        backup_cf = ttk.LabelFrame(color_backup_container, text="Application Settings", padding=15, relief=tk.SOLID,
                                   borderwidth=2)
        backup_cf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        var_backup = tk.BooleanVar(value=self.asm_settings.get('backup_executable', True))
        vars_dict['backup_executable'] = var_backup
        ttk.Checkbutton(backup_cf, text="Create backup when\npatching executable", variable=var_backup).pack(
            anchor=tk.W, pady=5)

        var_ignore_font = tk.BooleanVar(value=self.asm_settings.get('ignore_font_fix', False))
        vars_dict['ignore_font_fix'] = var_ignore_font
        ttk.Checkbutton(backup_cf, text="Ignore Font Fix", variable=var_ignore_font).pack(anchor=tk.W, pady=5)

        bf = ttk.Frame(mf)
        bf.grid(row=3, column=0, columnspan=3, pady=20)

        def save_settings():
            self.asm_settings.update({k: vars_dict[k].get() for k in vars_dict if
                                      k not in ['base_opacity', 'backup_executable', 'ignore_font_fix']})
            self.asm_settings['backup_executable'] = vars_dict['backup_executable'].get()
            self.asm_settings['ignore_font_fix'] = vars_dict['ignore_font_fix'].get()
            try:
                opacity = int(vars_dict['base_opacity'].get() or 255)
                opacity = max(0, min(255, opacity))
                r, g, b = self.argb_to_rgb(self.asm_settings['base_color_argb'])
                self.asm_settings['base_color_argb'] = self.rgb_to_argb(r, g, b, opacity)
            except:
                pass
            messagebox.showinfo("Success", "ASM Settings saved")
            w.destroy()

        ttk.Button(bf, text="Save", command=save_settings).pack(side=tk.LEFT, padx=5, ipady=5)
        ttk.Button(bf, text="Cancel", command=w.destroy).pack(side=tk.LEFT, padx=5, ipady=5)
        mf.columnconfigure(1, weight=1)
        self.settings_vars = vars_dict

    def _browse_and_scan(self, var):
        fp = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if not fp:
            return
        var.set(fp)
        found = self.scan_executable(fp)
        if found:
            msg = "Scan Results:\n"
            if 'njprint' in found:
                msg += f"✓ njPrint found at {found['njprint']}\n"
            if 'njprint_color' in found:
                msg += f"✓ njPrintColor found at {found['njprint_color']}\n"
            if 'base_color_argb' in found:
                msg += f"✓ Base Color found: {found['base_color_argb']}\n"
            msg += "\nUpdate settings automatically?"
            if messagebox.askyesno("Scan Complete", msg):
                if 'njprint' in found:
                    self.settings_vars['njprint_offset'].set(found['njprint'])
                if 'njprint_color' in found:
                    self.settings_vars['njprint_color_offset'].set(found['njprint_color'])
                if 'base_color_argb' in found:
                    self.settings_vars['base_color_argb'].set(found['base_color_argb'])
                    opacity = self.extract_alpha_from_argb(found['base_color_argb'])
                    self.settings_vars['base_opacity'].set(str(opacity))
        else:
            messagebox.showinfo("Scan", "No patterns found in executable")

    def scan_executable(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            nj_patterns = [
                bytes.fromhex('224f03e51d900c3f422f1b90fc300470 0825'),
                bytes.fromhex('224f1e900c3f1d9003e5422ffc300470 0825')
            ]
            njc_patterns = [bytes.fromhex('04d20b004222'), bytes.fromhex('03d20b004222')]
            found = {}
            for pattern in nj_patterns:
                idx = data.find(pattern)
                if idx != -1:
                    found['njprint'] = f"0x{idx + 0x8c010000:08x}"
                    break
            for i, pattern in enumerate(njc_patterns):
                idx = data.find(pattern)
                if idx != -1:
                    found['njprint_color'] = f"0x{idx + 0x8c010000:08x}"
                    color_offset = idx + 14 if i == 0 else idx + 10
                    if color_offset + 4 <= len(data):
                        color_val = struct.unpack('<I', data[color_offset:color_offset + 4])[0]
                        found['base_color_argb'] = f"{color_val:08x}"
                    break
            return found
        except Exception as e:
            print(f"Scan error: {e}")
            return {}

    def load_project(self, fp=None):
        if not fp:
            fp = filedialog.askopenfilename(filetypes=[("Project files", "*.prj"), ("All files", "*.*")])
            if not fp:
                return
        try:
            with open(fp, 'r') as f:
                pd = json.load(f)
            self.scenes = {int(k): v for k, v in pd.get('scenes', {0: []}).items()}
            self.scene_names = {int(k): v for k, v in pd.get('scene_names', {}).items()}

            loaded_asm = pd.get('asm_settings', {})
            self.asm_settings.update(loaded_asm)

            if 'empty_space_end' not in self.asm_settings:
                self.asm_settings['empty_space_end'] = '0x00'

            if 'backup_executable' not in self.asm_settings:
                self.asm_settings['backup_executable'] = True

            if 'ignore_font_fix' not in self.asm_settings:
                self.asm_settings['ignore_font_fix'] = False

            if not self.scenes:
                self.scenes = {0: []}
            self.current_scene = 0
            self.update_scene_combo()
            self.refresh_tree()
            # Auto-select first entry if available
            if self.subtitles:
                self.tree.selection_set("0")
                self.on_select()
            self.enable_all_controls()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project: {e}")

    def save_project(self):
        fp = filedialog.asksaveasfilename(filetypes=[("Project files", "*.prj")])
        if fp:
            try:
                # Ensure backup_executable is properly saved
                asm_to_save = dict(self.asm_settings)
                # Convert boolean to string representation for JSON compatibility if needed
                if isinstance(asm_to_save.get('backup_executable'), bool):
                    asm_to_save['backup_executable'] = asm_to_save['backup_executable']

                pd = {'scenes': self.scenes, 'scene_names': self.scene_names, 'asm_settings': asm_to_save}
                with open(fp, 'w') as f:
                    json.dump(pd, f, indent=2)
                messagebox.showinfo("Success", "Project saved")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {e}")

    def new_project(self):
        fp = filedialog.askopenfilename(filetypes=[("DC Executable", "*.BIN"), ("All files", "*.*")])
        if not fp:
            return
        if messagebox.askyesno("Confirm", "Start a new project with this executable?"):
            self.scenes = {0: []}
            self.scene_names = {0: "None"}
            self.current_scene = 0
            self.asm_settings = {'game_binary': fp, 'executable_base_offset': '0x8c010000',
                                 'empty_space_offset': '0x8C010000', 'empty_space_end': '0x00',
                                 'njprint_offset': '0x00000000',
                                 'njprint_color_offset': '0x00000000', 'timer_offset': '0x00000000',
                                 'base_color_argb': 'ffbfbfbf', 'game_fps': '60', 'backup_executable': True,
                                 'ignore_font_fix': False}
            found = self.scan_executable(fp)
            if found:
                msg = "Scan Results:\n"
                if 'njprint' in found:
                    msg += f"✓ njPrint found at {found['njprint']}\n"
                    self.asm_settings['njprint_offset'] = found['njprint']
                if 'njprint_color' in found:
                    msg += f"✓ njPrintColor found at {found['njprint_color']}\n"
                    self.asm_settings['njprint_color_offset'] = found['njprint_color']
                if 'base_color_argb' in found:
                    msg += f"✓ Base Color found: {found['base_color_argb']}\n"
                    self.asm_settings['base_color_argb'] = found['base_color_argb']
                messagebox.showinfo("Scan Complete", msg)
            self.update_scene_combo()
            self.refresh_tree()
            self.clear_edit_fields()
            # Auto-select first entry if available
            if self.subtitles:
                self.tree.selection_set("0")
                self.on_select()
            else:
                # Ensure all entry widgets are disabled when starting new project with no entries
                self.clear_edit_fields()
            self.enable_all_controls()

    def load_file(self):
        fp = filedialog.askopenfilename(filetypes=[("Project files", "*.prj"), ("All files", "*.*")])
        if not fp:
            return
        fp = Path(fp)
        if fp.suffix.lower() == '.prj':
            self.load_project(str(fp))
        else:
            messagebox.showerror("Error", "Unsupported file type. Use .prj")

    def apply_apostrophe_fix(self, executable):
        if self.asm_settings.get('ignore_font_fix', False):
            return executable

        pattern_v1 = bytes.fromhex('16 29 28 07 00 00 15 02 00 00 00 00 22 01 00 00 15 02 04 01')
        replacement_v1 = bytes.fromhex('16 29 28 07 00 00 15 02 00 00 00 00 22 01 00 00 00 00 00 00')

        pattern_v2 = bytes.fromhex(
            'FF FF CE B9 CE B9 CE B9 CE B9 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 FF FF 00 00 00 00 CE B9 00 00 00 00 CE B9 00 00 00 00 CE B9')
        replacement_v2 = bytes.fromhex(
            'FF FF CE B9 CE B9 CE B9 CE B9 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')

        idx_v1 = executable.find(pattern_v1)
        if idx_v1 != -1:
            msg = "Apostrophe Font V1 found in executable.\n\nApply Fix?"
            if messagebox.askyesno("Apostrophe Fix", msg):
                executable[idx_v1:idx_v1 + len(replacement_v1)] = replacement_v1
                messagebox.showinfo("Success", "V1 Fix applied successfully!")
                return executable

        idx_v2 = executable.find(pattern_v2)
        if idx_v2 != -1:
            msg = "Apostrophe Font V2 found in executable.\n\nApply Fix?"
            if messagebox.askyesno("Apostrophe Fix", msg):
                executable[idx_v2:idx_v2 + len(replacement_v2)] = replacement_v2
                messagebox.showinfo("Success", "V2 Fix applied successfully!")
                return executable

        return executable

    def save_output(self):
        has_any_subs = any(len(subs) > 0 for subs in self.scenes.values())
        if not has_any_subs:
            messagebox.showwarning("Warning", "No subtitles to save")
            return

        # Show progress message
        progress_window = tk.Toplevel(self.root)
        progress_window.withdraw()

        try:
            buffer = bytearray([
                0x22, 0x4F, 0x08, 0x42, 0x3B, 0xD0, 0x02, 0x60, 0x3C, 0xD7, 0x2C, 0x37, 0x72, 0x67, 0x3A, 0xD3, 0x2C,
                0x33, 0x02, 0xA0, 0x32, 0x63, 0x02, 0x77, 0x04, 0x73, 0x71, 0x61, 0x1D, 0x61, 0x16, 0x30, 0xF9, 0x89,
                0x30, 0x61, 0x32, 0xD7, 0x72, 0x67, 0x76, 0x2F, 0x31, 0x84, 0x08, 0x40, 0x35, 0xD7, 0x7E, 0x07, 0x2F,
                0xD0, 0x72, 0x20, 0x32, 0x84, 0x0C, 0x62, 0x33, 0x84, 0xFF, 0x88, 0x03, 0x8B, 0x01, 0xE7, 0x76, 0x2F,
                0x03, 0xA0, 0x00, 0xE4, 0x00, 0xE7, 0x76, 0x2F, 0x0C, 0x64, 0x28, 0x44, 0x2B, 0x24, 0x46, 0x2F, 0xD8,
                0x7F, 0xF3, 0x66, 0x63, 0x62, 0x08, 0x41, 0x28, 0xD0, 0x0C, 0x31, 0x13, 0x63, 0x32, 0x63, 0x00, 0xE8,
                0x30, 0x60, 0x01, 0x73, 0x08, 0x20, 0x20, 0x89, 0x0A, 0x88, 0x03, 0x89, 0x00, 0x26, 0x01, 0x76, 0xF6,
                0xAF, 0x01, 0x78, 0x00, 0xE0, 0x00, 0x26, 0x36, 0x2F, 0xF3, 0x65, 0x04, 0x75, 0xFC, 0x50, 0x00, 0x88,
                0x07, 0x89, 0x24, 0xE0, 0x88, 0x30, 0x01, 0x40, 0x02, 0x70, 0x03, 0x61, 0x2E, 0xE0, 0x14, 0x0F, 0xFB,
                0x54, 0x14, 0xD0, 0x0B, 0x40, 0x56, 0x2F, 0xFC, 0x54, 0x01, 0x74, 0x4C, 0x1F, 0xF6, 0x63, 0xF6, 0x63,
                0xF3, 0x66, 0xDB, 0xAF, 0x00, 0xE8, 0x00, 0xE0, 0x00, 0x26, 0xF3, 0x63, 0xFB, 0x50, 0x00, 0x88, 0x08,
                0x89, 0x24, 0xE0, 0x88, 0x30, 0x01, 0x40, 0x02, 0x70, 0xFA, 0x54, 0x4D, 0x67, 0x28, 0x40, 0x7B, 0x20,
                0x0A, 0x1F, 0xFA, 0x54, 0x06, 0xD0, 0x0B, 0x40, 0x36, 0x2F, 0x04, 0x7F, 0xF6, 0x67, 0x05, 0xD0, 0x72,
                0x20, 0x04, 0x7F, 0x28, 0x7F, 0x04, 0x7F, 0x26, 0x4F, 0x0B, 0x00, 0x09, 0x00, 0x00, 0x00])

            try:
                with open(self.asm_settings['game_binary'], 'rb') as f:
                    executable = bytearray(f.read())
            except Exception as e:
                messagebox.showerror("Error", f"Game Binary: {e}")
                return

            executable = self.apply_apostrophe_fix(executable)

            # Create backup if enabled
            if self.asm_settings.get('backup_executable', True):
                backup_filename = self.asm_settings['game_binary'].rsplit('.', 1)
                backup_filename = f"{backup_filename[0]}_backup.bin"

                try:
                    with open(backup_filename, 'wb') as f:
                        f.write(executable)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create backup: {e}")
                    return

            njprint_offset = int(self.asm_settings['njprint_offset'], 16)
            base_offset = int(self.asm_settings['executable_base_offset'], 16)
            njprint_color_offset = int(self.asm_settings['njprint_color_offset'], 16) - base_offset

            njprint_type = struct.unpack('<I', executable[njprint_color_offset:njprint_color_offset + 4])[0]
            njcol_ptr_off = njprint_color_offset + (18 if njprint_type == 0xbd204 else 14)
            ram_color_ptr = struct.unpack('<I', executable[njcol_ptr_off:njcol_ptr_off + 4])[0]

            timer_offset = int(self.asm_settings['timer_offset'], 16)

            buffer.extend(struct.pack('<I', njprint_offset))
            buffer.extend(struct.pack('<I', ram_color_ptr))
            buffer.extend(struct.pack('<I', timer_offset))

            cursor = len(buffer)

            all_scenes_data = self.scenes

            unique_colors_set = set()
            unique_texts = {0: b'\x00'}
            text_to_id = {b'': 0}

            for scene_subs in all_scenes_data.values():
                for sub in scene_subs:
                    color = sub.get('color', 'ffbfbfbf')
                    text_bytes = sub['text'].encode('utf-8')

                    if text_bytes not in text_to_id:
                        text_id = len(unique_texts)
                        unique_texts[text_id] = text_bytes + b'\x00'
                        text_to_id[text_bytes] = text_id

                    unique_colors_set.add(color)

            unique_colors = {color: idx for idx, color in enumerate(sorted(unique_colors_set))}

            num_scenes = len(all_scenes_data)

            ptr_ptr_sequence_offset = cursor
            buffer.extend(b'\x00' * 4)
            cursor += 4

            ptr_ptr_time_values_offset = cursor
            buffer.extend(b'\x00' * 4)
            cursor += 4

            ptr_ptr_subs_text_offset = cursor
            buffer.extend(b'\x00' * 4)
            cursor += 4

            ptr_color_table_offset = cursor
            buffer.extend(b'\x00' * 4)
            cursor += 4

            padding = (4 - (cursor % 4)) % 4
            buffer.extend(b'\x00' * padding)
            cursor += padding

            ptr_sequence_array_offset = cursor
            buffer.extend(b'\x00' * (num_scenes * 4))
            cursor += num_scenes * 4

            ptr_time_values_array_offset = cursor
            buffer.extend(b'\x00' * (num_scenes * 4))
            cursor += num_scenes * 4

            ptr_subs_text_array_offset = cursor
            buffer.extend(b'\x00' * (len(unique_texts) * 4))
            cursor += len(unique_texts) * 4

            sequence_offsets = {}
            time_value_offsets = {}
            game_fps = int(self.asm_settings.get('game_fps', '60'))

            for scene_idx in sorted(all_scenes_data.keys()):
                scene_subs = all_scenes_data[scene_idx]

                if not scene_subs:
                    padding = (4 - (cursor % 4)) % 4
                    buffer.extend(b'\x00' * padding)
                    cursor += padding
                    sequence_offsets[scene_idx] = cursor
                    buffer.extend(struct.pack('BBBB', 0, 0, 0, 0))
                    cursor += 4

                    padding = (4 - (cursor % 4)) % 4
                    buffer.extend(b'\x00' * padding)
                    cursor += padding
                    time_value_offsets[scene_idx] = cursor
                    buffer.extend(struct.pack('<H', 0xFFFF))
                    cursor += 2

                    padding = (4 - (cursor % 4)) % 4
                    buffer.extend(b'\x00' * padding)
                    cursor += padding
                    continue

                events = []
                for local_idx, sub in enumerate(scene_subs):
                    events.append((sub['start'], local_idx, 'start'))
                    events.append((sub['end'], local_idx, 'end'))
                events.sort()

                state_changes = [(0, ())]
                active_subs = set()

                for time, sub_idx, evt_type in events:
                    if evt_type == 'start':
                        active_subs.add(sub_idx)
                    else:
                        active_subs.discard(sub_idx)
                    state_changes.append((time, tuple(sorted(active_subs))))

                if state_changes[-1][1]:
                    state_changes.append((state_changes[-1][0], ()))

                padding = (4 - (cursor % 4)) % 4
                buffer.extend(b'\x00' * padding)
                cursor += padding

                sequence_offsets[scene_idx] = cursor

                for time, active_set in state_changes:
                    if active_set:
                        for sub_idx in active_set:
                            sub = scene_subs[sub_idx]
                            text_bytes = sub['text'].encode('utf-8')
                            text_id = text_to_id[text_bytes]
                            color = sub.get('color', 'ffbfbfbf')
                            color_id = unique_colors[color]
                            y = sub.get('y', 0) & 0xFF
                            x_val = sub.get('x', 0)
                            if sub.get('auto_center', True):
                                x = 0xFF
                            else:
                                x = x_val & 0xFF
                            buffer.extend(struct.pack('BBBB', text_id, color_id, y, x))
                            cursor += 4
                    else:
                        buffer.extend(struct.pack('BBBB', 0, 0, 0, 0))
                        cursor += 4

                padding = (4 - (cursor % 4)) % 4
                buffer.extend(b'\x00' * padding)
                cursor += padding

                time_value_offsets[scene_idx] = cursor

                for time, active_set in state_changes[1:]:
                    game_ticks = (time * game_fps) // 1000
                    if game_ticks > 0xFFFE:
                        game_ticks = 0xFFFE
                    buffer.extend(struct.pack('<H', game_ticks))
                    cursor += 2

                buffer.extend(struct.pack('<H', 0xFFFF))
                cursor += 2

                padding = (4 - (cursor % 4)) % 4
                buffer.extend(b'\x00' * padding)
                cursor += padding

            padding = (4 - (cursor % 4)) % 4
            buffer.extend(b'\x00' * padding)
            cursor += padding

            colors_offset = cursor
            for color in sorted(unique_colors.keys()):
                color_val = int(color, 16)
                buffer.extend(struct.pack('<I', color_val))
                cursor += 4

            padding = (4 - (cursor % 4)) % 4
            buffer.extend(b'\x00' * padding)
            cursor += padding

            text_offsets = {}
            for text_id in sorted(unique_texts.keys()):
                padding = (4 - (cursor % 4)) % 4
                buffer.extend(b'\x00' * padding)
                cursor += padding

                text_offsets[text_id] = cursor
                text_bytes = unique_texts[text_id]
                buffer.extend(text_bytes)
                cursor += len(text_bytes)

            empty_space_offset = int(self.asm_settings['empty_space_offset'], 16)
            empty_space_end = int(self.asm_settings['empty_space_end'], 16)
            base_offset_val = int(self.asm_settings['executable_base_offset'], 16)

            write_offset = empty_space_offset - base_offset_val

            available_space = empty_space_end - empty_space_offset
            final_buffer_length = len(buffer)

            if final_buffer_length > available_space:
                messagebox.showerror("Error",
                                     f"Buffer exceeds available space. Need {final_buffer_length} bytes, but only have {available_space} bytes available ({hex(empty_space_offset)} to {hex(empty_space_end)})")
                return

            ptr_sequence_array_addr = (empty_space_offset + ptr_sequence_array_offset) & 0xFFFFFFFF
            ptr_time_values_array_addr = (empty_space_offset + ptr_time_values_array_offset) & 0xFFFFFFFF
            ptr_subs_text_array_addr = (empty_space_offset + ptr_subs_text_array_offset) & 0xFFFFFFFF
            colors_addr = (empty_space_offset + colors_offset) & 0xFFFFFFFF

            buffer[ptr_ptr_sequence_offset:ptr_ptr_sequence_offset + 4] = struct.pack('<I', ptr_sequence_array_addr)
            buffer[ptr_ptr_time_values_offset:ptr_ptr_time_values_offset + 4] = struct.pack('<I',
                                                                                            ptr_time_values_array_addr)
            buffer[ptr_ptr_subs_text_offset:ptr_ptr_subs_text_offset + 4] = struct.pack('<I', ptr_subs_text_array_addr)
            buffer[ptr_color_table_offset:ptr_color_table_offset + 4] = struct.pack('<I', colors_addr)

            for scene_idx in sorted(all_scenes_data.keys()):
                offset = ptr_sequence_array_offset + (scene_idx * 4)
                seq_addr = (empty_space_offset + sequence_offsets[scene_idx]) & 0xFFFFFFFF
                buffer[offset:offset + 4] = struct.pack('<I', seq_addr)

            for scene_idx in sorted(all_scenes_data.keys()):
                offset = ptr_time_values_array_offset + (scene_idx * 4)
                time_addr = (empty_space_offset + time_value_offsets[scene_idx]) & 0xFFFFFFFF
                buffer[offset:offset + 4] = struct.pack('<I', time_addr)

            for text_id in sorted(unique_texts.keys()):
                offset = ptr_subs_text_array_offset + (text_id * 4)
                text_addr = (empty_space_offset + text_offsets[text_id]) & 0xFFFFFFFF
                buffer[offset:offset + 4] = struct.pack('<I', text_addr)

            padded_buffer = buffer + bytearray([0x00] * (available_space - final_buffer_length))

            if write_offset + len(padded_buffer) > len(executable):
                messagebox.showerror("Error",
                                     f"Padded buffer would exceed executable size. Need {write_offset + len(padded_buffer)} bytes, but executable is only {len(executable)} bytes")
                return

            executable[write_offset:write_offset + len(padded_buffer)] = padded_buffer

            output_file = self.asm_settings['game_binary']
            try:
                with open(output_file, 'wb') as f:
                    f.write(executable)
                progress_window.destroy()
                messagebox.showinfo("Success", f"Successfully patched:\n {output_file}")
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Error", f"Failed to write patched executable: {e}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            progress_window.destroy()
            messagebox.showerror("Error", f"Failed to export: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    root = tk.Tk()
    app = njSubs_Editor(root)
    root.mainloop()