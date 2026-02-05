import csv
import os
import sys
import traceback

# Import necessary libraries for Word document manipulation
try:
    from docxtpl import DocxTemplate
except ImportError:
    print("CRITICAL ERROR: 'docxtpl' needs to be installed.")
    sys.exit()

try:
    # Try to import libraries for merging multiple docs into one
    from docxcompose.composer import Composer
    from docx import Document as Document_compose
    SINGLE_FILE_MODE = True
except ImportError:
    # Fallback if docxcompose isn't installed
    SINGLE_FILE_MODE = False
    print("WARNING: 'docxcompose' not found. Merging functionality disabled.")

# --- HELPER FUNCTION ---
# Decides if text is a timing note to be moved to a header (e.g. "(Pre)")
def get_timing_tag(text):
    if not isinstance(text, str): return ""
    t = text.lower().strip()
    # Check for variations of "Pre-Performance"
    if ("pre" in t and "perf" in t) or "pre-" in t: return "(Pre)"
    # Check for variations of "Interval"
    if "int" in t or "interval" in t: return "(Int)"
    return ""

# --- MAIN PROCESSING FUNCTION ---
def process_and_generate(csv_path, template_path, output_path):
    print(f"Processing CSV: {csv_path}")
    
    # ===========================
    # PART 1: PARSE THE CSV FILE
    # ===========================
    try:
        # Open and read the entire CSV file into memory
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            all_lines = f.readlines()
    except Exception as e:
        raise Exception(f"Failed to read CSV file: {e}")

    # Find the start indices of each reservation block ("Anchors")
    pax_indices = []
    summary_index = len(all_lines)

    for i, line in enumerate(all_lines):
        # "Pax:" and "Arrival:" on the same line indicate a new booking header
        if "Pax:" in line and "Arrival:" in line:
            pax_indices.append(i)
        # Stop reading when we hit the report summary footer
        if "Report item summary" in line:
            summary_index = i
            break 

    reservations = []

    # Loop through each detected reservation block
    for i, current_pax_idx in enumerate(pax_indices):
        # Calculate start and end lines for this specific reservation
        start_idx = current_pax_idx - 2
        if i + 1 < len(pax_indices):
            end_idx = pax_indices[i + 1] - 2
        else:
            end_idx = summary_index

        # Slice the lines for this reservation
        res_lines = all_lines[start_idx:end_idx]
        
        # --- Extract Meta Data (Name, Table, Pax) ---
        try:
            # Line 0 is the guest name
            guest_name = res_lines[0].replace('"', '').strip()
            
            # Line 2 contains Table, Pax, and Time. Parse it as CSV.
            pax_row = next(csv.reader([res_lines[2]]))
            table_no = pax_row[0]
            # Extract just the number for pax
            pax = pax_row[2].replace('Pax: ', '')
        except:
            # If metadata is malformed, skip this block
            continue

        # --- Extract Food and Notes ---
        food_items = {'starters': [], 'mains': [], 'sides': [], 'desserts': [], 'drinks': []}
        timing_tags = {'starter_tag': '', 'main_tag': '', 'dessert_tag': ''}
        collected_notes = []

        # Iterate through the item lines (starting from line 3)
        for line in res_lines[3:]:
            if not line.strip(): continue # Skip empty lines
            try:
                row = next(csv.reader([line]))
            except: continue
            
            # Ensure row is not empty
            if not row: continue
            
            # Get the first column safely
            first_col = row[0].strip().lower()

            # --- NOTES LOGIC ---
            if "note" in first_col:
                 if len(row) > 1 and row[1].strip():
                     collected_notes.append(row[1].strip())
                 continue
            # ---------------------------
            
            # Safety check: Food items must have at least 3 columns (Type, Item, Qty)
            if len(row) < 3: continue 
            if first_col == "type": continue 

            item_name = row[1].strip()

            # --- CRUSH WATER FILTER ---
            # If the template is 'Crush', skip Still/Sparkling water
            if "crush" in template_path.lower():
                if "still water" in item_name.lower() or "sparkling water" in item_name.lower():
                    continue 
            # -------------------------------

            # --- TIMING TAGS LOGIC ---
            raw_col_4 = row[4] if len(row) > 4 else ""
            current_timing_tag = get_timing_tag(raw_col_4)

            # Create the dish object
            dish_obj = {'qty': row[2], 'dish': item_name, 'dietary': ""}

            # Categorize the item and apply header tags if found
            if 'starter' in first_col: 
                food_items['starters'].append(dish_obj)
                if current_timing_tag and not timing_tags['starter_tag']:
                    timing_tags['starter_tag'] = current_timing_tag
            elif 'main' in first_col: 
                food_items['mains'].append(dish_obj)
                if current_timing_tag and not timing_tags['main_tag']:
                    timing_tags['main_tag'] = current_timing_tag
            elif 'side' in first_col: 
                food_items['sides'].append(dish_obj)
            elif 'dessert' in first_col: 
                food_items['desserts'].append(dish_obj)
                if current_timing_tag and not timing_tags['dessert_tag']:
                    timing_tags['dessert_tag'] = current_timing_tag
            elif 'drink' in first_col or 'wine' in first_col:
                food_items['drinks'].append(dish_obj)

        # NOTE: The "Phantom Main" fix has been REMOVED here.
        # This relies on the Word Template using {% if mains %} to hide the header.

        # Add the completely processed reservation to the master list
        reservations.append({
            'name': guest_name,
            'table': table_no,
            'pax': pax,
            'notes': "\n".join(collected_notes),
            **timing_tags,
            **food_items
        })

    if not reservations:
         raise Exception("No valid reservations found in the CSV file.")

    # ===========================
    # PART 2: GENERATE THE WORD DOCUMENT
    # ===========================
    if not os.path.exists(template_path):
         raise Exception("Selected template file not found on server.")

    try:
        # 1. Create the master document with the first reservation
        master = DocxTemplate(template_path)
        master.render(reservations[0])
        master.save(output_path)

        # 2. If there are more reservations, append them
        if len(reservations) > 1 and SINGLE_FILE_MODE:
            composer = Composer(Document_compose(output_path))
            
            for res in reservations[1:]:
                temp = DocxTemplate(template_path)
                temp.render(res)
                
                # Create a temporary file for this single card
                temp_card_path = output_path.replace('.docx', f'_temp_{res["table"]}.docx')
                temp.save(temp_card_path)
                
                # Append the new card
                composer.doc.add_page_break()
                composer.append(Document_compose(temp_card_path))
                
                # Clean up the temporary file immediately
                if os.path.exists(temp_card_path):
                    os.remove(temp_card_path)
            
            # Save the final multi-page document
            composer.save(output_path)
            
    except Exception as e:
         raise Exception(f"Error generating Word document: {e}")

    return True