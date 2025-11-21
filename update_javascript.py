import re

# Read the current index.html from templates directory
with open('core/templates/index.html', 'r') as file:
    content = file.read()

# Update API_CONFIG section
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

# Update makeApiRequest function
new_make_api_request = '''// FIXED API request function
const makeApiRequest = async (endpoint, method = 'GET', data = null) => {
    // Clean the endpoint - remove leading and trailing slashes
    let cleanEndpoint = endpoint.replace(/^\\/+|\\/+$/g, '');
    
    // Build the URL properly
    const url = `${API_CONFIG.BASE_URL}/${cleanEndpoint}`;
    console.log('🚀 Making API request to:', url, 'Method:', method);
    
    const options = {
        method,
        headers: API_CONFIG.HEADERS
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('❌ API request error:', error);
        console.error('❌ Failed URL:', url);
        updateApiStatus('disconnected');
        
        // For demo purposes, return simulated data if API is down
        console.log('🔄 Using simulated data as fallback');
        return getSimulatedData(endpoint);
    }
};'''

# Replace makeApiRequest function
content = re.sub(r'const makeApiRequest = async[^{]*{[^}]*}[^}]*}[^}]*};', new_make_api_request, content, flags=re.DOTALL)

# Add debug function after the makeApiRequest function
debug_function = '''
// Add this debug function
const debugApiSetup = () => {
    console.log('🔧 ===== API SETUP DEBUG =====');
    console.log('🔧 BASE_URL:', API_CONFIG.BASE_URL);
    console.log('🔧 Full events URL:', `${API_CONFIG.BASE_URL}/events`);
    console.log('🔧 Full locations URL:', `${API_CONFIG.BASE_URL}/partylocations`);
    console.log('🔧 Full legacy locations URL:', `${API_CONFIG.BASE_URL}/locations`);
    console.log('🔧 Available endpoints should be:');
    console.log('🔧   - http://127.0.0.1:8000/api/events/');
    console.log('🔧   - http://127.0.0.1:8000/api/partylocations/');
    console.log('🔧   - http://127.0.0.1:8000/api/locations/');
    console.log('🔧 ===========================');
};

// Call this when your app starts
debugApiSetup();'''

# Insert debug function after makeApiRequest
make_api_request_end = content.find('const makeApiRequest = async')
if make_api_request_end != -1:
    # Find the end of the makeApiRequest function
    func_end = content.find('};', make_api_request_end) + 2
    content = content[:func_end] + debug_function + content[func_end:]

# Write the updated content back
with open('core/templates/index.html', 'w') as file:
    file.write(content)

print("JavaScript API configuration updated successfully!")
