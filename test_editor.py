#!/usr/bin/env python3
"""
Simple test to verify subtitle editor opens
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os

def test_subtitle_editor():
    root = tk.Tk()
    root.title("Test Subtitle Editor")
    root.geometry("600x400")
    
    def open_editor():
        try:
            # Create a simple test editor window
            editor = tk.Toplevel(root)
            editor.title("Subtitle Editor Test")
            editor.geometry("800x600")
            editor.transient(root)
            editor.grab_set()
            
            # Add some test content
            ttk.Label(editor, text="Subtitle Editor Test Window", font=('Arial', 16, 'bold')).pack(pady=20)
            
            # Time entry
            time_frame = ttk.Frame(editor)
            time_frame.pack(pady=10)
            
            ttk.Label(time_frame, text="Start Time:").pack(side=tk.LEFT, padx=5)
            start_entry = ttk.Entry(time_frame, width=12)
            start_entry.pack(side=tk.LEFT, padx=5)
            start_entry.insert(0, "00:00:00")
            
            ttk.Label(time_frame, text="End Time:").pack(side=tk.LEFT, padx=5)
            end_entry = ttk.Entry(time_frame, width=12)
            end_entry.pack(side=tk.LEFT, padx=5)
            end_entry.insert(0, "00:00:03")
            
            # Text entry
            ttk.Label(editor, text="Subtitle Text:").pack(pady=5)
            text_widget = tk.Text(editor, height=4, width=60)
            text_widget.pack(pady=5)
            text_widget.insert("1.0", "Type your subtitle text here...")
            
            # Add button
            def add_subtitle():
                start = start_entry.get()
                end = end_entry.get()
                text = text_widget.get("1.0", tk.END).strip()
                messagebox.showinfo("Subtitle Added", f"Start: {start}\nEnd: {end}\nText: {text}")
            
            ttk.Button(editor, text="Add Subtitle", command=add_subtitle).pack(pady=10)
            
            print("Subtitle editor window opened successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open editor: {str(e)}")
            print(f"Error: {e}")
    
    # Main window
    ttk.Label(root, text="Test Subtitle Editor", font=('Arial', 14, 'bold')).pack(pady=20)
    ttk.Button(root, text="Open Subtitle Editor", command=open_editor).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    test_editor()
