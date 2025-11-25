import csv
import os
from docxtpl import DocxTemplate

# Try to import the merger tool. If it fails, we will just make separate files.
try:
    from docxcompose.composer import Composer
    from docx import Document as Document_compose
    SINGLE_FILE_MODE = True
except ImportError:
    SINGLE_FILE_MODE = False
    print("WARNING: 'docxcompose' not found. Generating separate files instead.")


# CONFIGURATION

INPUT_CSV_FILE = 'kitchen-sheet-2025-11-25-(10_00-22_00).csv'
TEMPLATE_DOC_FILE = 'Balcony Cards.docx'
OUTPUT_FOLDER = 'Printed_Cards'
OUTPUT_FILENAME = 'BAL_Table_Cards.docx'
DEBUG_FILE = 'debug_check.txt'

def clean_text(text):
    if not text: return ""
    return text.replace('"', '').strip()

def parse_kitchen_sheet(file_path):
    print(f"Reading file: {file_path}...")
    reservations = []
    debug_messages = []
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            all_lines = f.readlines()
    except FileNotFoundError:
        print(f"ERROR: Could not find file '{file_path}'.")
        return [], ["File not found"]

    # 1. IDENTIFY ANCHORS
    pax_indices = []
    summary_index = len(all_lines)

    for i, line in enumerate(all_lines):
        if "Pax:" in line and "Arrival:" in line:
            pax_indices.append(i)
        if "Report item summary" in line:
            summary_index = i
            break 

    print(f"Found {len(pax_indices)} reservation blocks.")

    # 2. PROCESS RESERVATIONS
    for i, current_pax_idx in enumerate(pax_indices):
        start_idx = current_pax_idx - 2
        if i + 1 < len(pax_indices):
            end_idx = pax_indices[i + 1] - 2
        else:
            end_idx = summary_index

        res_lines = all_lines[start_idx:end_idx]
        
        # A. Meta Data
        guest_name = clean_text(res_lines[0])
        pax_line = res_lines[2]
        meta_reader = csv.reader([pax_line])
        meta_row = next(meta_reader)

        try:
            table_no = meta_row[0]
            pax = meta_row[2].replace('Pax: ', '')
            time_val = meta_row[3].replace('Arrival: ', '')
        except IndexError:
            table_no = "Unknown"
            pax = "0"
            time_val = "??"

        # B. Food Data & Comments
        food_items = {'starters': [], 'mains': [], 'sides': [], 'desserts': [], 'drinks': []}
        collected_notes = []

        for line_idx in range(3, len(res_lines)):
            line = res_lines[line_idx].strip()
            if not line: continue 
            
            reader = csv.reader([line])
            try:
                row = next(reader)
            except StopIteration:
                continue

            if len(row) < 2: continue # Skip broken lines

            # Check for Customer Notes 
            first_col = row[0].strip().lower()
            if "customer preorder notes" in first_col:
                # The note is in the second column
                if len(row) > 1:
                    collected_notes.append(row[1])
                continue

            # Standard Food Processing
            if len(row) < 3: continue
            if first_col == "type": continue 

            cat_type = first_col
            item_name = row[1]
            qty = row[2]
            for_who = row[4] if len(row) > 4 else ""
            dietary = row[5] if len(row) > 5 else ""

            dish_obj = {'qty': qty, 'dish': item_name, 'for_who': for_who, 'dietary': dietary}

            if 'starter' in cat_type: food_items['starters'].append(dish_obj)
            elif 'main' in cat_type: food_items['mains'].append(dish_obj)
            elif 'side' in cat_type: food_items['sides'].append(dish_obj)
            elif 'dessert' in cat_type: food_items['desserts'].append(dish_obj)
            elif 'drink' in cat_type: food_items['drinks'].append(dish_obj)

        # Join all notes found into one string
        notes_string = "\n".join(collected_notes)

        # Log
        total_food = len(food_items['starters']) + len(food_items['mains'])
        log_msg = f"Table {table_no} ({guest_name}): {total_food} items. Notes: {notes_string if notes_string else 'None'}"
        print(log_msg)
        debug_messages.append(log_msg)

        reservations.append({
            'name': guest_name,
            'table': table_no,
            'pax': pax,
            'time': time_val,
            'notes': notes_string,  # <--- Added to dictionary
            **food_items
        })

    return reservations, debug_messages

def generate_output(data, debug_log):
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    with open(DEBUG_FILE, 'w') as f:
        f.write("\n".join(debug_log))

    if not data: return

    # STRATEGY: TRY SINGLE FILE, FALLBACK TO MULTIPLE
    if SINGLE_FILE_MODE:
        try:
            print(f"\nMerging {len(data)} cards into one file: {OUTPUT_FILENAME}")
            
            # Master file (First card)
            master_template = DocxTemplate(TEMPLATE_DOC_FILE)
            master_template.render(data[0])
            master_template.save(OUTPUT_FILENAME)

            master_doc = Document_compose(OUTPUT_FILENAME)
            composer = Composer(master_doc)

            # Append rest
            for res in data[1:]:
                temp_template = DocxTemplate(TEMPLATE_DOC_FILE)
                temp_template.render(res)
                temp_filename = "temp_card_render.docx"
                temp_template.save(temp_filename)
                
                composer.doc.add_page_break()
                composer.append(Document_compose(temp_filename))
                
                if os.path.exists(temp_filename): os.remove(temp_filename)
            
            composer.save(OUTPUT_FILENAME)
            print("SUCCESS! Created Single File.")
            return
        except Exception as e:
            print(f"Merge failed ({e}). Falling back to separate files.")

    # FALLBACK: Generate Separate Files
    print(f"\nGenerating separate files in '{OUTPUT_FOLDER}'...")
    doc = DocxTemplate(TEMPLATE_DOC_FILE)
    for res in data:
        doc.render(res)
        safe_name = "".join([c for c in res['name'] if c.isalpha() or c.isdigit() or c==' ']).strip().replace(" ", "_")
        doc.save(f"{OUTPUT_FOLDER}/Table_{res['table']}_{safe_name}.docx")
    print("Done.")

if __name__ == "__main__":
    print("--- Restaurant Card Automation ---")
    data, log = parse_kitchen_sheet(INPUT_CSV_FILE)
    if data: generate_output(data, log)