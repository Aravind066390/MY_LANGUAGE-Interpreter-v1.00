import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import subprocess
import threading
import os

# ---------- Globals ----------
selected_folder = None  # Folder where .exe, .c, and .txt live

# ---------- Functions ----------
def select_folder():
    """Let user select the folder containing n.exe, n.c, and n.txt"""
    global selected_folder
    folder = filedialog.askdirectory(title="Select Project Folder")
    if folder:
        selected_folder = folder
        root.title(f"MyLang IDE - {selected_folder}")
        status_var.set(f"Project folder: {selected_folder}")
    else:
        messagebox.showwarning("Warning", "No folder selected!")

def open_file():
    """Open an existing code file (inside selected folder)"""
    global selected_folder
    if not selected_folder:
        messagebox.showwarning("Warning", "Select a folder first!")
        return

    # Open file only within selected folder
    file_path = filedialog.askopenfilename(
        initialdir=selected_folder,
        title="Open MyLang file",
        filetypes=[("MyLang Files", ".txt"), ("All Files", ".*")]
    )
    if file_path:
        try:
            with open(file_path, "r") as f:
                code_text.delete(1.0, tk.END)
                code_text.insert(tk.END, f.read())
            root.title(f"MyLang IDE - {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")

def save_file():
    """Save code into n.txt inside selected folder"""
    global selected_folder
    if not selected_folder:
        messagebox.showwarning("Warning", "Select a folder first!")
        return

    file_path = os.path.join(selected_folder, "n.txt")
    try:
        with open(file_path, "w") as f:
            f.write(code_text.get(1.0, tk.END))
        root.title(f"MyLang IDE - {file_path}")
        messagebox.showinfo("Saved", f"File saved as {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save file:\n{e}")

def run_code(interactive=False):
    def target():
        global selected_folder
        if not selected_folder:
            messagebox.showwarning("Warning", "Select a folder first!")
            return

        code_file = os.path.join(selected_folder, "n.txt")
        source_file = os.path.join(selected_folder, "n.c")
        interpreter_path = os.path.join(selected_folder, "n.exe")
        gcc_path = "C:/Program Files/CodeBlocks/MinGW/bin/gcc.exe"  # adjust if needed

        # Save code to n.txt
        with open(code_file, "w") as f:
            f.write(code_text.get(1.0, tk.END))

        try:
            # Compile if n.c exists
            if os.path.exists(source_file):
                compile_result = subprocess.run(
                    [gcc_path, source_file, "-o", interpreter_path],
                    capture_output=True, text=True
                )
                if compile_result.returncode != 0:
                    output_text.delete(1.0, tk.END)
                    output_text.insert(tk.END, "---COMPILATION ERRORS---\n")
                    output_text.insert(tk.END, compile_result.stderr)
                    return

            if not os.path.exists(interpreter_path):
                messagebox.showerror("Error", f"Interpreter not found at {interpreter_path}")
                return

            output_text.delete(1.0, tk.END)

            if not interactive:
                # Non-interactive execution
                proc = subprocess.run(
                    [interpreter_path, code_file],
                    capture_output=True,
                    text=True
                )
                output_text.insert(tk.END, proc.stdout)
                if proc.stderr:
                    output_text.insert(tk.END, "\n---RUNTIME ERRORS---\n" + proc.stderr)

            else:
                # Interactive: repeatedly ask user for input as needed
                proc = subprocess.Popen(
                    [interpreter_path, code_file],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Collect input values until user cancels
                while True:
                    value = simpledialog.askstring("Program Input", "Enter next input (Cancel to stop):")
                    if value is None:  # User cancelled
                        break
                    proc.stdin.write(value + "\n")
                    proc.stdin.flush()
                    output_text.insert(tk.END, f"[INPUT] {value}\n")

                # Read final outputs
                out, err = proc.communicate()
                if out:
                    output_text.insert(tk.END, out)
                if err:
                    output_text.insert(tk.END, "\n---RUNTIME ERRORS---\n" + err)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    threading.Thread(target=target).start()

# ---------- GUI ----------
root = tk.Tk()
root.title("MyLang IDE")
root.geometry("800x600")

menu = tk.Menu(root)
root.config(menu=menu)

file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Select Folder", command=select_folder)
file_menu.add_command(label="Open", command=open_file)
file_menu.add_command(label="Save", command=save_file)
file_menu.add_command(label="Exit", command=root.quit)

code_text = tk.Text(root, height=20)
code_text.pack(fill=tk.BOTH, expand=True)

run_btn = tk.Button(root, text="Run (Non-interactive)", command=lambda: run_code(False))
run_btn.pack(pady=5)
run_btn_int = tk.Button(root, text="Run (Interactive)", command=lambda: run_code(True))
run_btn_int.pack(pady=5)

output_text = tk.Text(root, height=10, bg="#f0f0f0")
output_text.pack(fill=tk.BOTH, expand=True)

# Status bar
status_var = tk.StringVar(value="No project folder selected")
tk.Label(root, textvariable=status_var, anchor='w').pack(fill=tk.X, side=tk.BOTTOM)

root.mainloop()