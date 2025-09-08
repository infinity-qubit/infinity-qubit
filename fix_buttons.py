#!/usr/bin/env python3
"""
Script to add activebackground properties to all tk.Button instances that don't have them
"""

import os
import re

def fix_buttons_in_file(file_path):
    """Fix buttons in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match tk.Button definitions that have bg but not activebackground
    # This is a complex regex to handle multi-line button definitions
    button_pattern = r'(tk\.Button\([^)]+?)(\))'
    
    def replace_button(match):
        button_def = match.group(1)
        closing_paren = match.group(2)
        
        # Check if it already has activebackground
        if 'activebackground' in button_def:
            return match.group(0)  # No change needed
        
        # Check if it has bg parameter
        if 'bg=' not in button_def:
            return match.group(0)  # No bg, so don't add activebackground
        
        # Add activebackground before the closing parenthesis
        # Default to button_hover_background from palette
        activebackground_line = ",\n                                activebackground=palette['button_hover_background'], activeforeground=palette['button_text_color']"
        
        return button_def + activebackground_line + closing_paren
    
    # Apply the replacement
    content = re.sub(button_pattern, replace_button, content, flags=re.DOTALL)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed buttons in {file_path}")
        return True
    
    return False

def main():
    """Fix all button files"""
    src_dir = "/Users/bogdanivanescu/Documents/Dev/Pers/infinity-qubit/src"
    
    python_files = [
        'puzzle_mode.py',
        'sandbox_mode.py',
        'tutorial.py',
        'learn_hub.py',
        'game_mode_selection.py'
    ]
    
    for file_name in python_files:
        file_path = os.path.join(src_dir, file_name)
        if os.path.exists(file_path):
            try:
                if fix_buttons_in_file(file_path):
                    print(f"✓ Updated {file_name}")
                else:
                    print(f"- No changes needed in {file_name}")
            except Exception as e:
                print(f"✗ Error processing {file_name}: {e}")

if __name__ == "__main__":
    main()
