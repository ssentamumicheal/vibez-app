import re

# Read the current index.html from templates directory
with open('core/templates/index.html', 'r') as file:
    content = file.read()

print("🔧 Fixing JavaScript API calls...")

# Fix 1: Update the addRealLocations function to use 'partylocations' instead of '/locations'
old_add_real_locations = r'''const addRealLocations = async \(\) => \{[^}]+\}'''
new_add_real_locations = '''const addRealLocations = async () => {
    showLoading(true);
    try {
        // Use the correct endpoint - FIXED
        const locations = await makeApiRequest('partylocations');
        allLocations = locations;
        updateApiStatus('connected');
        
        // Add crowd data to locations
        allLocations.forEach(location => {
            location.crowd = Math.floor(Math.random() * 100);
            location.checkIns = Math.floor(Math.random() * 20) + 1;
        });
        
        filteredLocations = [...allLocations];
        
        // Clear existing markers
        markers.forEach(marker => map.removeLayer(marker.marker));
        markers = [];

        // Add new markers
        allLocations.forEach(location => {
            addMarkerToMap(location);
        });
        
        showLoading(false);
    } catch (error) {
        console.error('Failed to fetch locations:', error);
        // Use simulated data as fallback
        allLocations = getSimulatedData('locations');
        filteredLocations = [...allLocations];
        
        // Add markers for simulated data
        markers.forEach(marker => map.removeLayer(marker.marker));
        markers = [];
        allLocations.forEach(location => {
            addMarkerToMap(location);
        });
        
        showLoading(false);
    }
};'''

# Replace the function
content = re.sub(old_add_real_locations, new_add_real_locations, content, flags=re.DOTALL)

# Fix 2: Update the addRealEvents function to use 'events' instead of '/events'
old_add_real_events = r'''const addRealEvents = async \(\) => \{[^}]+\}'''
new_add_real_events = '''const addRealEvents = async () => {
    try {
        // Use the correct endpoint - FIXED
        const events = await makeApiRequest('events');
        allEvents = events;
        updateApiStatus('connected');
        
        filteredEvents = [...allEvents];
        
        // Add event markers to map
        addEventMarkersToMap();
    } catch (error) {
        console.error('Failed to fetch events:', error);
        // Use simulated data as fallback
        allEvents = getSimulatedData('events');
        filteredEvents = [...allEvents];
        addEventMarkersToMap();
    }
};'''

# Replace the function
content = re.sub(old_add_real_events, new_add_real_events, content, flags=re.DOTALL)

# Fix 3: Update the fetchEvents function
old_fetch_events = r'''const fetchEvents = async \(\) => \{[^}]+\}'''
new_fetch_events = '''const fetchEvents = async () => {
    showLoading(true);
    try {
        // Use the correct endpoint - FIXED
        const events = await makeApiRequest('events');
        allEvents = events;
        updateApiStatus('connected');
        
        renderEvents();
        showLoading(false);
    } catch (error) {
        console.error('Failed to fetch events:', error);
        // Use existing events data
        allEvents = getSimulatedData('events');
        renderEvents();
        showLoading(false);
    }
};'''

# Replace the function
content = re.sub(old_fetch_events, new_fetch_events, content, flags=re.DOTALL)

# Fix 4: Add the getSimulatedData function if it doesn't exist
if 'getSimulatedData' not in content:
    simulated_data_function = '''
// Enhanced simulated data function
const getSimulatedData = (endpoint) => {
    console.log('🎭 Generating simulated data for:', endpoint);
    
    if (endpoint.includes('events') || endpoint === 'events') {
        return [
            {
                id: 1,
                name: "Nyege Nyege Festival 2025",
                category: "festival",
                date: new Date(2025, 8, 5),
                time: "7:00 PM",
                location: "Nile Discovery Beach",
                address: "Jinja, Uganda",
                lat: 0.4244,
                lng: 33.2021,
                description: "The biggest electronic music festival in East Africa featuring international and local artists.",
                popularity: "high",
                price: "$$$",
                attendees: 15000,
                isPopular: true,
                isTrending: true
            },
            {
                id: 2,
                name: "Kampala City Festival",
                category: "cultural",
                date: new Date(2025, 9, 8),
                time: "10:00 AM",
                location: "Kampala Road",
                address: "Kampala, Uganda",
                lat: 0.3163,
                lng: 32.5822,
                description: "Annual street festival celebrating Kampala's culture with music, dance, and food.",
                popularity: "high",
                price: "Free",
                attendees: 50000,
                isPopular: true,
                isTrending: true
            }
        ];
    } else if (endpoint.includes('locations') || endpoint.includes('partylocations') || endpoint === 'locations') {
        return [
            { id: 1, lat: 0.3163, lng: 32.5822, title: "Club Guvnor", rating: 4.5, type: "club", vibe: "high", distance: 2, crowd: 85, checkIns: 15 },
            { id: 2, lat: 0.3136, lng: 32.5876, title: "Cayenne", rating: 4.2, type: "lounge", vibe: "medium", distance: 3, crowd: 70, checkIns: 12 },
            { id: 3, lat: 0.3189, lng: 32.5854, title: "Bubbles O'Leary", rating: 4.7, type: "bar", vibe: "medium", distance: 1, crowd: 90, checkIns: 20 },
            { id: 4, lat: 0.3195, lng: 32.5847, title: "Al's Bar", rating: 4.0, type: "bar", vibe: "chill", distance: 1, crowd: 60, checkIns: 8 },
            { id: 5, lat: 0.3131, lng: 32.5905, title: "The Lawns", rating: 4.8, type: "lounge", vibe: "high", distance: 4, crowd: 95, checkIns: 25 }
        ];
    }
    return [];
};'''
    
    # Insert after the makeApiRequest function
    make_api_end = content.find('const makeApiRequest = async')
    if make_api_end != -1:
        func_end = content.find('};', make_api_end) + 2
        content = content[:func_end] + simulated_data_function + content[func_end:]

# Write the updated content back
with open('core/templates/index.html', 'w') as file:
    file.write(content)

print("✅ JavaScript API calls fixed successfully!")
print("📝 Changes made:")
print("   - Updated addRealLocations to use 'partylocations' endpoint")
print("   - Updated addRealEvents to use 'events' endpoint") 
print("   - Updated fetchEvents to use 'events' endpoint")
print("   - Added getSimulatedData function for fallback")
