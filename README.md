I coded this tool to fix our messy service prep. It scans the raw kitchen CSVs (ignoring the weird formatting), extracts guest orders and allergy notes, and fills out a Word template automatically. It then merges everything into one print-ready file. What used to take us an hour of copy-pasting now takes two minutes.

**How it Works**

The input data comes from a kitchen management system export. The file is technically a CSV, but it is formatted like a visual report with blank lines, headers, and footers, which makes it impossible to open correctly in Excel or process with standard tools.

To solve this, the script uses a linear scanning approach. It reads the file line-by-line and looks for specific text anchors (like "Pax:" and "Arrival:") to locate reservation blocks. This allows it to reliably extract:

Guest Name and Table Number

Party Size (Pax)

Food orders (sorted into Starters, Mains, Sides, Desserts)

Drinks

Dietary requirements and customer notes

Once the data is extracted, it uses docxtpl to fill out a Microsoft Word template. This keeps the design separate from the code—if we need to change the font or logo on the cards, we just edit the Word file directly.

Finally, it uses docxcompose to merge all the individual cards into a single document so they can be printed in one batch.

**Project Structure**

card_maker.py: The main Python script.

Balcony Cards.docx: The Word template. It uses Jinja2 tags (like {{ name }}) to know where to put the data.

kitchen-sheet.csv: The input file from the kitchen system.

Printed_Cards/: The folder where the output file is saved.

**Setup and Usage**

Install the required libraries:

pip install docxtpl docxcompose


Place your latest kitchen report in the folder and rename it (or update the filename in the script).

Run the script:

python card_maker.py


Open All_Table_Cards.docx and print.

**Notes on the Code**

I used a linear scanner instead of a block-based splitter for parsing the CSV. Initially, splitting by blank lines caused issues because the number of blank lines in the report varies. Scanning for keywords proved to be much more stable.

The script also includes a fallback mode: if the library for merging files (docxcompose) isn't found or fails, it will generate individual Word files for each table so that service isn't disrupted.
