import os
import re

# --- Configuration ---
# The folder where your individual .svg icons are stored.
SOURCE_ICON_DIR = "static/Icons/source" 

# The path where the final combined sprite will be saved.
DEST_SPRITE_FILE = "static/Conflux-Icons.svg"

# --- Main Script Logic ---

def create_sprite():
    """
    Finds all .svg files in the source directory, cleans their content using
    regular expressions, and combines them into a single SVG sprite file.
    """
    print("Starting robust SVG sprite build process...")

    # Ensure the source directory exists
    if not os.path.isdir(SOURCE_ICON_DIR):
        print(f"Error: Source directory not found at '{SOURCE_ICON_DIR}'")
        return

    # A list to hold the cleaned <symbol> strings
    all_symbols = []

    try:
        svg_files = [f for f in os.listdir(SOURCE_ICON_DIR) if f.endswith('.svg')]
        if not svg_files:
            print(f"Warning: No .svg files found in '{SOURCE_ICON_DIR}'.")
            return
    except Exception as e:
        print(f"Error reading source directory: {e}")
        return

    # Loop through each .svg file
    for filename in svg_files:
        try:
            # Read the entire content of the SVG file as text
            with open(os.path.join(SOURCE_ICON_DIR, filename), 'r', encoding='utf-8') as f:
                content = f.read()

            # Use regex to find the viewBox attribute from the original <svg> tag
            viewbox_match = re.search(r'viewBox="([^"]+)"', content)
            viewbox = viewbox_match.group(1) if viewbox_match else "0 0 24 24" # Default if not found

            # Use regex to extract everything INSIDE the main <svg> tag
            inner_content_match = re.search(r'<svg[^>]*>(.*?)<\/svg>', content, re.DOTALL)
            inner_content = inner_content_match.group(1) if inner_content_match else ""

            # Use regex to remove all fill="..." and stroke="..." attributes to make the SVG stylable with CSS
            inner_content = re.sub(r'\s(fill|stroke)="[^"]+"', '', inner_content)
            
            # Create a unique ID for the symbol from the filename
            symbol_id = os.path.splitext(filename)[0].removesuffix('-svgrepo-com')

            # Assemble the final <symbol> tag
            symbol_str = f'  <symbol id="{symbol_id}" viewBox="{viewbox}">{inner_content.strip()}</symbol>'
            all_symbols.append(symbol_str)
            print(f"  Processed '{filename}' -> symbol id='{symbol_id}'")

        except Exception as e:
            print(f"  Error processing '{filename}': {e}")
            continue

    # Assemble the final sprite file content
    sprite_header = '<svg xmlns="http://www.w3.org/2000/svg" style="display: none;">\n'
    sprite_footer = '\n</svg>'
    final_content = sprite_header + '\n'.join(all_symbols) + sprite_footer

    # Write the final combined sprite to the destination file
    try:
        with open(DEST_SPRITE_FILE, 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"\nBuild complete! Sprite saved to '{DEST_SPRITE_FILE}'")
    except Exception as e:
        print(f"\nError writing final sprite file: {e}")

# This allows the script to be run from the command line
if __name__ == '__main__':
    create_sprite()
