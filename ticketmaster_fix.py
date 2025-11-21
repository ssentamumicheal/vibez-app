class TicketMasterService:
    def __init__(self):
        # For Apigee Edge, we need to use Basic Auth with Consumer Key and Secret
        self.consumer_key = '7mmwork/OAxGbYB4OxyI0C6jGtHexVOxy'
        self.consumer_secret = 'fLmWbS8hqwHyO7k'
        self.base_url = 'https://7mmwork-oaxgbyb4oxyi0c6jgthexvoxy.apigee.io/discovery/v2/'
    
    def search_events(self, city='Kampala', classification_name='Music', size=20):
        """Fetch events from Ticketmaster API through Apigee"""
        try:
            # For Apigee, we might need to use the base URL directly
            # Let's try a simpler approach first
            params = {
                'city': city,
                'classificationName': classification_name,
                'size': size,
                'sort': 'date,asc'
            }
            
            # Using Basic Auth for Apigee
            auth = (self.consumer_key, self.consumer_secret)
            
            response = requests.get(
                f"{self.base_url}events.json", 
                params=params, 
                auth=auth,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_events(data)
            else:
                print(f"Ticketmaster API error: {response.status_code} - {response.text}")
                # Fallback to mock data for development
                return self._get_mock_events()
                
        except requests.RequestException as e:
            print(f"Error fetching from Ticketmaster: {e}")
            # Fallback to mock data
            return self._get_mock_events()
    
    def _parse_events(self, data):
        """Parse Ticketmaster events into our format"""
        events = []
        
        try:
            # Handle different response formats
            if '_embedded' in data and 'events' in data['_embedded']:
                events_data = data['_embedded']['events']
            elif 'events' in data:
                events_data = data['events']
            else:
                events_data = data  # Assume it's already a list of events
            
            for event_data in events_data:
                try:
                    # Extract venue information safely
                    venues = event_data.get('_embedded', {}).get('venues', [{}])
                    venue = venues[0] if venues else {}
                    
                    # Parse date safely
                    start_info = event_data.get('dates', {}).get('start', {})
                    start_date = start_info.get('dateTime') or start_info.get('localDate')
                    
                    event = {
                        'id': f"tm_{event_data.get('id', '')}",
                        'name': event_data.get('name', 'Unknown Event'),
                        'description': event_data.get('info', '') or event_data.get('description', ''),
                        'start_date': start_date,
                        'venue_name': venue.get('name', 'Unknown Venue'),
                        'venue_address': self._format_address(venue),
                        'venue_lat': venue.get('location', {}).get('latitude'),
                        'venue_lng': venue.get('location', {}).get('longitude'),
                        'images': [img['url'] for img in event_data.get('images', []) if img.get('url')],
                        'url': event_data.get('url', ''),
                        'price_range': event_data.get('priceRanges', [{}])[0],
                        'source': 'ticketmaster'
                    }
                    
                    # Only add events with valid dates
                    if event['start_date']:
                        events.append(event)
                        
                except (KeyError, IndexError, AttributeError) as e:
                    print(f"Error parsing event: {e}")
                    continue
        
        except Exception as e:
            print(f"Error processing events data: {e}")
        
        return events
    
    def _format_address(self, venue):
        """Format venue address"""
        address_parts = []
        if venue.get('address', {}).get('line1'):
            address_parts.append(venue['address']['line1'])
        if venue.get('city', {}).get('name'):
            address_parts.append(venue['city']['name'])
        if venue.get('country', {}).get('name'):
            address_parts.append(venue['country']['name'])
        
        return ', '.join(address_parts) if address_parts else 'Address not available'
    
    def _get_mock_events(self):
        """Provide mock events for development when API fails"""
        return [
            {
                'id': 'tm_mock_1',
                'name': 'Kampala Music Festival',
                'description': 'Annual music festival featuring local and international artists',
                'start_date': '2025-12-15T19:00:00',
                'venue_name': 'Lugogo Cricket Oval',
                'venue_address': 'Lugogo, Kampala, Uganda',
                'venue_lat': 0.3254,
                'venue_lng': 32.5825,
                'images': [],
                'url': 'https://example.com',
                'source': 'ticketmaster_mock'
            },
            {
                'id': 'tm_mock_2',
                'name': 'Afrobeat Night',
                'description': 'Night of the best Afrobeat music with DJs and live performances',
                'start_date': '2025-12-20T21:00:00',
                'venue_name': 'The Hive',
                'venue_address': 'Industrial Area, Kampala, Uganda',
                'venue_lat': 0.3174,
                'venue_lng': 32.5829,
                'images': [],
                'url': 'https://example.com',
                'source': 'ticketmaster_mock'
            }
        ]
