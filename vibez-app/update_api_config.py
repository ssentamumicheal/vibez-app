import re

# Read the current index.html
with open('core/templates/index.html', 'r') as file:
    content = file.read()

# Find and replace the API_CONFIG section
new_api_config = '''// API Configuration - COMPLETELY FIXED
const API_CONFIG = {
    CONSUMER_KEY: '7IxmuowYQAzGbY84Qwj0lCGjGHbxVQxv',
    CONSUMER_SECRET: 'fLmWbSB1qw1lyO7k',
    BASE_URL: 'http://127.0.0.1:8000/api', // NO trailing slash
    HEADERS: {
        'Content-Type': 'application/json',
        'X-API-Key': '7IxmuowYQAzGbY84Qwj0lCGjGHbxVQxv'
    }
};'''

# Replace the API_CONFIG section
content = re.sub(r'const API_CONFIG = {[^}]*};', new_api_config, content, flags=re.DOTALL)

# Write back
with open('core/templates/index.html', 'w') as file:
    file.write(content)

print("✅ API_CONFIG updated successfully!")
