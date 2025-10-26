import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import subprocess
import threading
import os
import time
def get_selected_folder():
    return getattr(root, "selected_folder", None)
def set_selected_folder(folder):
    """Set folder, change current working dir and update UI."""
    root.selected_folder = folder
    if folder:
        try:
            os.chdir(folder)  # ensure file dialogs default to this folder
        except Exception:
            pass
        root.title(f"MyLang IDE - {folder}")
        status_var.set(f"Project folder: {folder}")
        # auto-load n.txt if exists
        ntxt = os.path.join(folder, "n.txt")
        if os.path.exists(ntxt):
            try:
                with open(ntxt, "r", encoding="utf-8") as f:
                    code_text.delete(1.0, tk.END)
                    code_text.insert(tk.END, f.read())
            except Exception:
                pass
    else:
        root.title("MyLang IDE")
        status_var.set("No project folder selected")

# ---------- Functions ----------
def select_folder():
    folder = filedialog.askdirectory(title="Select your project folder")
    if folder:
        set_selected_folder(folder)
    else:
        # If user cancels, just leave it unselected — they can choose later
        messagebox.showinfo("Info", "No folder selected. Use File → Select Folder to choose later.")

def open_file():
    folder = get_selected_folder()
    if not folder:
        messagebox.showwarning("Warning", "Select a project folder first (File → Select Folder).")
        return
    file_path = filedialog.askopenfilename(
        initialdir=folder,
        title="Open MyLang file (from project folder)",
        filetypes=[("MyLang Files", ".txt"), ("All Files", ".*")]
    )
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_text.delete(1.0, tk.END)
                code_text.insert(tk.END, f.read())
            root.title(f"MyLang IDE - {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")

def save_file():
    folder = get_selected_folder()
    if not folder:
        messagebox.showwarning("Warning", "Select a project folder first (File → Select Folder).")
        return
    # Save directly to n.txt in selected folder
    file_path = os.path.join(folder, "n.txt")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_text.get(1.0, tk.END))
        root.title(f"MyLang IDE - {file_path}")
        messagebox.showinfo("Saved", f"Saved to {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save file:\n{e}")

def save_as():
    folder = get_selected_folder()
    initial = folder if folder else os.getcwd()
    file_path = filedialog.asksaveasfilename(
        initialdir=initial,
        defaultextension=".txt",
        filetypes=[("MyLang Files", ".txt"), ("All Files", ".*")]
    )
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code_text.get(1.0, tk.END))
            root.title(f"MyLang IDE - {file_path}")
            messagebox.showinfo("Saved", f"Saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

def run_code(interactive=False):
    """Run the interpreter in the selected folder. Interactive mode prompts when a prompt line ends with ':'"""
    def target():
        folder = get_selected_folder()
        if not folder:
            messagebox.showwarning("Warning", "Select a project folder first (File → Select Folder).")
            return

        code_file = os.path.join(folder, "n.txt")
        interpreter_path = os.path.join(folder, "n.exe")

        # Always save current editor into n.txt before running
        try:
            with open(code_file, "w", encoding="utf-8") as f:
                f.write(code_text.get(1.0, tk.END))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write n.txt:\n{e}")
            return

        if not os.path.exists(interpreter_path):
            messagebox.showerror("Error", f"Interpreter (n.exe) not found in selected folder:\n{interpreter_path}")
            return

        output_text.delete(1.0, tk.END)

        try:
            if not interactive:
                # Non-interactive: run and capture output
                proc = subprocess.run(
                    [interpreter_path, code_file],
                    capture_output=True,
                    text=True,
                    encoding="utf-8"
                )
                if proc.stdout:
                    output_text.insert(tk.END, proc.stdout)
                if proc.stderr:
                    output_text.insert(tk.END, "\n---RUNTIME ERRORS---\n" + proc.stderr)
            else:
                # Interactive: stream stdout and prompt user when interpreter prints a prompt (line ending with ':')
                proc = subprocess.Popen(
                    [interpreter_path, code_file],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    bufsize=1
                )
                while True:
                    line = proc.stdout.readline()
                    if line:
                        output_text.insert(tk.END, line)
                        output_text.see(tk.END)
                        if line.rstrip().endswith(":"):
                            user_input = simpledialog.askstring("Input Required", "Enter input (Cancel to send empty):")
                            if user_input is None:
                                user_input = ""
                            try:
                                proc.stdin.write(user_input + "\n")
                                proc.stdin.flush()
                                output_text.insert(tk.END, f"[INPUT] {user_input}\n")
                                output_text.see(tk.END)
                            except Exception:
                                break
                    else:
                        if proc.poll() is not None:
                            break
                        time.sleep(0.01)
                err = proc.stderr.read()
                if err:
                    output_text.insert(tk.END, "\n---RUNTIME ERRORS---\n" + err)

        except Exception as e:
            messagebox.showerror("Error", str(e))
    threading.Thread(target=target, daemon=True).start()
root = tk.Tk()
root.title("MyLang IDE")
root.geometry("900x650")
menu = tk.Menu(root)
root.config(menu=menu)
file_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Select Folder", command=select_folder)
file_menu.add_separator()
file_menu.add_command(label="Open (from folder)", command=open_file)
file_menu.add_command(label="Save (to n.txt)", command=save_file)
file_menu.add_command(label="Save As...", command=save_as)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
toolbar = tk.Frame(root)
toolbar.pack(fill=tk.X, padx=4, pady=4)
select_btn = tk.Button(toolbar, text="Select Folder", command=select_folder)
select_btn.pack(side=tk.LEFT, padx=2)
open_btn = tk.Button(toolbar, text="Open", command=open_file)
open_btn.pack(side=tk.LEFT, padx=2)
save_btn = tk.Button(toolbar, text="Save", command=save_file)
save_btn.pack(side=tk.LEFT, padx=2)
code_text = tk.Text(root, height=20, wrap='none')
code_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
run_frame = tk.Frame(root)
run_frame.pack(fill=tk.X, padx=6, pady=(0,6))
run_btn = tk.Button(run_frame, text="Run (Non-interactive)", command=lambda: run_code(False))
run_btn.pack(side=tk.LEFT, padx=4)
run_btn_int = tk.Button(run_frame, text="Run (Interactive)", command=lambda: run_code(True))
run_btn_int.pack(side=tk.LEFT, padx=4)
output_text = tk.Text(root, height=12, bg="#f7f7f7", wrap='none')
output_text.pack(fill=tk.BOTH, expand=False, padx=6, pady=(0,6))
status_var = tk.StringVar(value="No project folder selected")
status_bar = tk.Label(root, textvariable=status_var, anchor='w')
status_bar.pack(fill=tk.X, side=tk.BOTTOM)
root.after(100, select_folder)

root.mainloop()