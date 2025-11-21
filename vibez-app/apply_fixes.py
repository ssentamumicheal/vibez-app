#!/usr/bin/env python3
import re
import sys

def apply_fixes(html_file):
    with open(html_file, 'r') as f:
        content = f.read()
    
    # Read the fixes
    with open('fix_apis.js', 'r') as f:
        fixes_content = f.read()
    
    # Extract individual functions from fixes
    functions = {}
    current_function = None
    current_content = []
    
    for line in fixes_content.split('\n'):
        if line.strip().startswith('const ') and '=' in line and '=>' in line:
            if current_function:
                functions[current_function] = '\n'.join(current_content)
            # Extract function name
            func_name = line.split('=')[0].strip().split(' ')[1]
            current_function = func_name
            current_content = [line]
        elif current_function:
            current_content.append(line)
    
    if current_function:
        functions[current_function] = '\n'.join(current_content)
    
    # Apply each function replacement
    for func_name, func_content in functions.items():
        # Create regex pattern to find the function
        pattern = r'const ' + re.escape(func_name) + r'[^{]*\{[^}]*\}'
        
        # Try to find and replace
        old_pattern = re.search(pattern, content, re.DOTALL)
        if old_pattern:
            content = content.replace(old_pattern.group(0), func_content)
            print(f"✓ Replaced function: {func_name}")
        else:
            # If not found, try to insert before the API_CONFIG declaration
            api_config_pos = content.find('const API_CONFIG =')
            if api_config_pos != -1:
                # Find the position before API_CONFIG
                insert_pos = content.rfind('\n', 0, api_config_pos)
                content = content[:insert_pos] + '\n' + func_content + '\n' + content[insert_pos:]
                print(f"✓ Added function: {func_name}")
            else:
                print(f"✗ Could not find placement for: {func_name}")
    
    # Write the updated content
    with open(html_file, 'w') as f:
        f.write(content)
    
    print("✓ Fixes applied successfully!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 apply_fixes.py <html_file>")
        sys.exit(1)
    
    apply_fixes(sys.argv[1])
