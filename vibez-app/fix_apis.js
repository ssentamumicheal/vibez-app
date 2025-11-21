// Fix for Ticketmaster API and Location Services

// Replace the fetchEventsFromTicketmaster function
const fetchEventsFromTicketmaster = async (lat, lon, radius = 50) => {
    try {
        // First, let's try to get the user's country code based on coordinates
        const countryCode = await getCountryCode(lat, lon);
        
        const params = new URLSearchParams({
            apikey: API_CONFIG.TICKETMASTER_API_KEY,
            latlong: `${lat},${lon}`,
            radius: radius,
            unit: 'miles',
            size: '20',
            sort: 'date,asc',
            classificationName: 'music,comedy,festival',
            countryCode: countryCode || 'US'
        });

        console.log('Fetching events from Ticketmaster with params:', params.toString());
        
        const response = await fetch(`${API_CONFIG.TICKETMASTER_BASE_URL}?${params}`);

        if (!response.ok) {
            throw new Error(`Ticketmaster API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        
        if (data._embedded && data._embedded.events) {
            console.log(`Found ${data._embedded.events.length} events from Ticketmaster`);
            return data._embedded.events.map(event => {
                const venue = event._embedded.venues[0];
                const startDate = new Date(event.dates.start.dateTime || event.dates.start.localDate);
                
                // Get price info safely
                let priceInfo = 'Price varies';
                if (event.priceRanges && event.priceRanges.length > 0) {
                    const minPrice = event.priceRanges[0].min || 0;
                    const maxPrice = event.priceRanges[0].max || minPrice;
                    priceInfo = `$${minPrice} - $${maxPrice}`;
                }

                return {
                    id: event.id,
                    name: event.name,
                    description: event.info || event.description || 'No description available',
                    category: getEventCategory(event.classifications),
                    startDate: startDate,
                    endDate: new Date(startDate.getTime() + (event.dates.start.approximateDuration || 3 * 60 * 60 * 1000)),
                    time: startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    location: venue.name,
                    address: `${venue.city.name}, ${venue.state ? venue.state.stateCode : venue.country.countryCode}`,
                    lat: parseFloat(venue.location.latitude),
                    lng: parseFloat(venue.location.longitude),
                    price: priceInfo,
                    attendees: event._embedded.venues[0].upcomingEvents?.total || Math.floor(Math.random() * 1000) + 100,
                    isPopular: event._embedded.venues[0].upcomingEvents?.total > 1000,
                    isTrending: Math.random() > 0.7,
                    image: event.images && event.images.length > 0 ? event.images[0].url : null
                };
            });
        } else {
            console.log('No events found in Ticketmaster response, using sample data');
            return getSampleEvents(lat, lon);
        }
    } catch (error) {
        console.error('Error fetching events from Ticketmaster:', error);
        showNotification('Using sample events data', 'info');
        return getSampleEvents(lat, lon);
    }
};

// Helper functions
const getCountryCode = async (lat, lon) => {
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
        const data = await response.json();
        return data.address?.country_code?.toUpperCase();
    } catch (error) {
        console.error('Error getting country code:', error);
        return 'US';
    }
};

const getEventCategory = (classifications) => {
    if (!classifications || !classifications[0]) return 'music';
    
    const segment = classifications[0].segment?.name?.toLowerCase();
    const genre = classifications[0].genre?.name?.toLowerCase();
    
    if (segment === 'music') return 'music';
    if (segment === 'arts' || segment === 'theatre') return 'cultural';
    if (genre === 'comedy') return 'comedy';
    if (segment === 'sports') return 'sports';
    
    return 'music';
};

// Improved location permission function
const requestLocationPermission = () => {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by this browser'));
            return;
        }
        
        if (userLocation && (Date.now() - userLocation.timestamp < 300000)) {
            resolve(userLocation);
            return;
        }
        
        const options = {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000
        };
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const newLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    timestamp: new Date(),
                    userId: currentUser?.userId,
                    username: currentUser?.username
                };
                
                userLocation = newLocation;
                resolve(newLocation);
            },
            (error) => {
                let errorMessage = 'Unable to get your location';
                
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = 'Location access denied. Please enable location permissions in your browser settings.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = 'Location information is unavailable.';
                        break;
                    case error.TIMEOUT:
                        errorMessage = 'Location request timed out.';
                        break;
                    default:
                        errorMessage = 'An unknown error occurred while getting your location.';
                        break;
                }
                
                reject(new Error(errorMessage));
            },
            options
        );
    });
};

// Fallback location function
const getApproximateLocation = async () => {
    try {
        showNotification('Getting approximate location...', 'info');
        
        const response = await fetch('https://ipapi.co/json/');
        const data = await response.json();
        
        userLocation = {
            lat: data.latitude,
            lng: data.longitude,
            accuracy: 50000,
            timestamp: new Date(),
            source: 'ip'
        };
        
        if (map) {
            map.setView([userLocation.lat, userLocation.lng], 10);
            await loadRealData(userLocation.lat, userLocation.lng);
        }
    } catch (error) {
        console.error('Failed to get approximate location:', error);
        userLocation = {
            lat: 0.3476,
            lng: 32.5825,
            accuracy: null,
            timestamp: new Date(),
            source: 'default'
        };
        await loadRealData(userLocation.lat, userLocation.lng);
    }
};
