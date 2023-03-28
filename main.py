import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog
import shutil
import glob
import os
# Create the database
conn = sqlite3.connect('data.db')
c = conn.cursor()

# Create table
c.execute('''CREATE TABLE IF NOT EXISTS data 
            (id INTEGER PRIMARY KEY, material TEXT , wfs REAL, ts REAL, ctwd REAL, file TEXT)''')
conn.commit()

# Function to retrieve data from the database based on dropdown selection
def retrieve_data(selection):
    c.execute("SELECT * FROM data WHERE file=?", (selection,))
    return c.fetchall()


# Function to create the GUI
def create_gui():
    
    def save_data():
        arr = ", ".join([name[1] for name in label_names[1:]])
        res=[]
        for label_name,data_entry in zip(label_names[1:],data_entries): 
            if label_name[2]=='TEXT':
                res.append(data_entry.get()) if data_entry.get()!='' else res.append('')
            elif label_name[2]=='INTEGER':
                res.append(int(data_entry.get())) if data_entry.get()!='' else res.append('')
            elif label_name[2]=='REAL':
                res.append(float(data_entry.get())) if data_entry.get()!='' else res.append('')
        
        c.execute("INSERT INTO data ("+arr+") VALUES ("+', '.join(['?' for i in data_entries])+")", res)
        conn.commit()
        refresh_dropdowns()
        root.destroy()
        create_gui()
    
    

    def refresh_dropdowns():
        for idx,(label_name,file_dropdown) in enumerate(zip(label_names,file_dropdowns)):
            data_options = []
            
            arr,res=[],[]
            for name,f in zip(label_names[:idx]+label_names[idx+1:],file_dropdowns[:idx]+file_dropdowns[idx+1:]):
                if f.get() != '':
                    arr.append(name[1]+"=? AND")
                    res.append(f.get())
            arr = " ".join(arr)[:-4]
            if arr !='': 
                c.execute("SELECT DISTINCT "+label_name[1]+" FROM data WHERE "+arr,res)
                rows = c.fetchall()
                data_options.append('')
                for row in rows:
                    data_options.append(row[0])
                file_dropdown.config(values=data_options)
        

    # Create the main window
    root = tk.Tk()
    root.title("Welding database v0")

    # Create labels and entries for data input
    c.execute("PRAGMA table_info(data)")
    '''loadout'''
    for i in range(11):
        title_label = ttk.Label(root, text="      ")
        title_label.grid(column=i, row=0, padx=5, pady=5)
    title_label = ttk.Label(root, text="Data input interface")
    title_label.grid(column=1, row=0, padx=5, pady=5)
    
    title_label = ttk.Label(root, text="Data search interface")
    title_label.grid(column=5, row=0, padx=5, pady=5)
    title_label = ttk.Label(root, text="Data view interface")
    title_label.grid(column=9, row=0, padx=5, pady=5)
    # Fetch all the column names
    '''Data input interface'''
    label_names = c.fetchall()
    data_entries = []
    for idx,label_name in enumerate(label_names[1:]):
        data_label = ttk.Label(root, text=str(label_name[0])+" "+label_name[1]+"("+label_name[2]+"):")
        data_label.grid(column=0, row=1+idx, padx=5, pady=5)
        data_entry = ttk.Entry(root)
        data_entry.grid(column=1, row=1+idx, padx=5, pady=5)
        data_entries.append(data_entry)
        if 'file' in label_name[1]:
            def browse_file(entry_idx):
                file_path = filedialog.askopenfilename()
                data_entries[entry_idx].delete(0, tk.END)
                data_entries[entry_idx].insert(0, file_path)
            file_button = ttk.Button(root, text="Browse", command = lambda entry_idx=idx: browse_file(entry_idx))
            file_button.grid(column=2, row=1+idx, padx=5, pady=5)
    save_button = ttk.Button(root, text="Save Data", command=save_data)
    save_button.grid(column=1, row=1+idx+1, padx=5, pady=5)

    add_entry = ttk.Entry(root, text="Enter Label Name:")
    add_entry.grid(column=0, row=1+idx+2, padx=5, pady=5)
    selected_option = tk.StringVar()
    selected_option.set('REAL')
    add_type = tk.OptionMenu(root, selected_option, 'REAL', 'TEXT', 'INTEGER')
    add_type.grid(column=1, row=1+idx+2, padx=5, pady=5)
    def add_column():
        c.execute("ALTER TABLE data ADD COLUMN "+add_entry.get()+" "+selected_option.get())
        conn.commit()
        root.destroy()
        create_gui()
    add_button = ttk.Button(root, text="Add Label", command=add_column)
    add_button.grid(column=2, row=1+idx+2, padx=5, pady=5)

    column_order=[name for name in label_names[1:]]
    del_dropdown = ttk.Combobox(root, values=['']+column_order)
    del_dropdown.current(0)
    del_dropdown.grid(column=0, row=1+idx+3, padx=5, pady=5)
    def del_column():
        c.execute("ALTER TABLE data DROP COLUMN "+del_dropdown.get().split(' ')[1])
        conn.commit()
        root.destroy()
        create_gui()
    del_button = ttk.Button(root, text="Del Label", command=del_column)
    del_button.grid(column=1, row=1+idx+3, padx=5, pady=5)

    
    idx_order = [int(name[0]) for name in label_names[1:]]
    sort_dropdown = ttk.Combobox(root, values=['']+column_order)
    sort_dropdown.current(0)
    sort_dropdown.grid(column=0, row=1+idx+4, padx=5, pady=5)
    idx_dropdown = ttk.Combobox(root, values=['']+idx_order)
    idx_dropdown.current(0)
    idx_dropdown.grid(column=1, row=1+idx+4, padx=5, pady=5)
    def sort_column():
        if sort_dropdown.get() =='':return
        label_idx = int(sort_dropdown.get().split(' ')[0])-1
        new_idx = int(idx_dropdown.get().split(' ')[0])-1
        label = [column_order[label_idx]]
        custom_order=column_order[:label_idx]+column_order[label_idx+1:]
        custom_order=custom_order[:new_idx]+label+custom_order[new_idx:]
        [c.execute("ALTER TABLE data RENAME COLUMN "+custom[1]+" TO temp_column"+str(custom[0])+"") for custom in custom_order]
        [c.execute("ALTER TABLE data ADD COLUMN "+custom[1]+" "+custom[2]+"") for custom in custom_order]
        [c.execute("UPDATE data SET "+custom[1]+" = temp_column"+str(custom[0])+"") for custom in custom_order]
        [c.execute("ALTER TABLE data DROP COLUMN temp_column"+str(custom[0])+"") for custom in custom_order]
        conn.commit()
        root.destroy()
        create_gui()
    sort_button = ttk.Button(root, text="Sort Label", command=sort_column)
    sort_button.grid(column=2, row=1+idx+4, padx=5, pady=5)

    os.makedirs('backups',exist_ok=True)
    def backup_dataset():
        backup_num = len(glob.glob('backups/data*.db'))
        shutil.copyfile('data.db','backups/data'+str(backup_num+1)+'.db')
        root.destroy()
        create_gui()
    backup_button = ttk.Button(root, text="Backup dataset", command=backup_dataset)
    backup_button.grid(column=2, row=1+idx+5, padx=5, pady=5)

    
    '''Data search interface'''
    # Create dropdown boxes for file selection
    file_dropdowns = []
    for idx,label_name in enumerate(label_names): 
        options = ['']
        c.execute("SELECT DISTINCT "+label_name[1]+" FROM data")
        rows = c.fetchall()
        for row in rows:
            options.append(row[0])
        data_label = ttk.Label(root, text="Select "+label_name[1]+":")
        data_label.grid(column=5, row=1+idx, padx=5, pady=5)
        file_dropdown = ttk.Combobox(root, values=options)
        file_dropdown.grid(column=6, row=1+idx, padx=5, pady=5)
        file_dropdown.bind("<<ComboboxSelected>>", lambda event: refresh_dropdowns())
        file_dropdowns.append(file_dropdown)

    # Create button to del data
    c.execute("SELECT * FROM data ")
    rows = c.fetchall()
    all_data_options=['']
    for row in rows:
        all_data_options.append(row)
    data_dropdown = ttk.Combobox(root, values=all_data_options)
    data_dropdown.current(0)
    data_dropdown.grid(column=5, row=1+idx+1, padx=5, pady=5)
    def output_data():
        output_id = data_dropdown.get().split(' ')[0]
        conn.commit()
        root.destroy()
        create_gui()
    output_data_button = ttk.Button(root, text="Output data", command=output_data)
    output_data_button.grid(column=6, row=1+idx+1, padx=5, pady=5)

    def del_data():
        del_id = data_dropdown.get().split(' ')[0]
        c.execute("DELETE FROM data WHERE id = "+del_id)
        c.execute("UPDATE data SET id = (id - 1) WHERE id > "+del_id+"")
        conn.commit()
        root.destroy()
        create_gui()
    del_data_button = ttk.Button(root, text="Del data", command=del_data)
    del_data_button.grid(column=6, row=1+idx+2, padx=5, pady=5)

    '''data display interface'''
    # Create labels to display count and data
    count_label = ttk.Label(root, text="Data size: ")
    count_label.grid(column=8, row=1+1, padx=5, pady=5)

    # Create button to read data
    data_labels=[]
    for i in range(20):
        data_label = ttk.Label(root, text="")
        data_label.grid(column=9, row=1+i, padx=5, pady=5)
        data_labels.append(data_label)
    page_c_label = ttk.Label(root, text="Pages: 1")
    page_c_label.grid(column=8, row=1+2, padx=5, pady=5)
    page_label = ttk.Label(root, text="Total pages: 1")
    page_label.grid(column=8, row=1+3, padx=5, pady=5)
    def read_data(data_labels):
        page_c = int(page_c_label.cget("text").split(' ')[1])
        arr,res=[],[]
        for name,f in zip(label_names,file_dropdowns):
            if f.get() != '':
                arr.append(name[1]+"=? AND")
                res.append(f.get())
        arr = " ".join(arr)[:-4]
        if arr=='':
            c.execute("SELECT COUNT(*) FROM data ")
        else:
            c.execute("SELECT COUNT(*) FROM data WHERE "+arr, res)
        count = c.fetchone()[0]
        count_label.config(text="Data size: "+str(count))

        if arr=='':
            c.execute("SELECT * FROM data ")
        else:
            c.execute("SELECT * FROM data WHERE "+arr, res)
        data = c.fetchall()
        page_label.config(text="Total pages: "+str(1+int((len(data)-0.5)/20)))
        [data_label.config(text="") for data_label in data_labels]
        for i,label in enumerate(data[int((page_c-1)*20):int(page_c*20)]):
            data_labels[i].config(text=label)

        #refresh data selection dropdown box
        data_dropdown.config(values=data[int((page_c-1)*20):int(page_c*20)])
    read_button = ttk.Button(root, text="Read Data", command= lambda data_labels=data_labels:read_data(data_labels))
    read_button.grid(column=8, row=1+0, padx=5, pady=5)
    def prev_page(data_labels):
        c_page = int(page_c_label.cget("text").split(' ')[1])
        new_page = max(c_page-1,1)
        page_c_label.config(text="Pages: "+str(new_page))
        read_data(data_labels)
    def next_page(data_labels):
        total_page = int(page_label.cget("text").split(' ')[2])
        c_page = int(page_c_label.cget("text").split(' ')[1])
        new_page = min(c_page+1,total_page)
        page_c_label.config(text="Pages: "+str(new_page))
        read_data(data_labels)
    prev_page_button = ttk.Button(root, text="Prev page", command= lambda data_labels=data_labels:prev_page(data_labels))
    prev_page_button.grid(column=8, row=1+4, padx=5, pady=5)
    next_page_button = ttk.Button(root, text="Next page", command= lambda data_labels=data_labels:next_page(data_labels))
    next_page_button.grid(column=8, row=1+5, padx=5, pady=5)
    

    

    # Start the GUI
    root.mainloop()

create_gui()