import json

# Read object array from color JSON
def get_colors_from_file(file_path):
    """Read colors from a JSON file and return as an object list"""
    with open(file_path, 'r') as file:
        palette_list = json.load(file)
    return palette_list

# Search palette for specific stage
def extract_color_palette(palette_list, stage_name):
    """Extract color palette for a specific stage"""
    for stage in palette_list:
        if stage['stage_name'] == stage_name:
            return stage['colors']
    return None