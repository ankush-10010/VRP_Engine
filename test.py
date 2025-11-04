import time
import random
import json
import threading
from datetime import datetime, timedelta
from hybrid_solver import assign_new_order_realtime, calculate_route_cost, batch_optimization_vrp

# --- Configuration ---
SIMULATION_START_HOUR = 9
SIMULATION_END_HOUR = 17
MINUTES_PER_TICK = 15
PROBABILITY_OF_NEW_ORDER_PER_TICK = 0.9
NUM_VEHICLES = 4
TIME_MATRIX_FILE = 'time_matrix.json'
MAX_ROUTE_DURATION_MINS = 150
MAX_STOPS_PER_ROUTE = 10
LAYER_2_INTERVAL_SECONDS = 20
OUTPUT_HTML_FILE = 'hybrid_simulation_live.html'
GOOGLE_MAPS_API_KEY = 'AIzaSyC_hI6BowrJPojeBiRldmuFVf3aqsSRZbg'  # Replace with your Google Maps API key

# --- Shared State ---
current_routes = {}
pending_orders = []
state_lock = threading.Lock()
simulation_running = True
simulation_events = []

# --- HTML Generation Functions ---
def format_time(minutes_from_start):
    """Convert minutes from 9:00 AM to readable time"""
    start = datetime.strptime("09:00", "%H:%M")
    result = start + timedelta(minutes=minutes_from_start)
    return result.strftime("%I:%M %p")

def generate_route_coordinates(route, locations):
    """Generate coordinate pairs for a route"""
    coords = []
    
    # Determine the correct key names for coordinates
    # Check if location has 'lat'/'lng' or 'latitude'/'longitude' or other variants
    sample_loc = locations[0]
    if 'lat' in sample_loc and 'lng' in sample_loc:
        lat_key, lng_key = 'lat', 'lng'
    elif 'latitude' in sample_loc and 'longitude' in sample_loc:
        lat_key, lng_key = 'latitude', 'longitude'
    elif 'lat' in sample_loc and 'lon' in sample_loc:
        lat_key, lng_key = 'lat', 'lon'
    else:
        # Try to find coordinate keys
        print(f"Available keys in location data: {sample_loc.keys()}")
        raise KeyError(f"Could not find coordinate keys in location data. Available keys: {list(sample_loc.keys())}")
    
    # Add depot at start
    coords.append({
        'lat': locations[0][lat_key],
        'lng': locations[0][lng_key],
        'address': locations[0]['original_address'],
        'type': 'depot',
        'index': 0
    })
    # Add all stops
    for idx in route:
        coords.append({
            'lat': locations[idx][lat_key],
            'lng': locations[idx][lng_key],
            'address': locations[idx]['original_address'],
            'type': 'stop',
            'index': idx
        })
    # Add depot at end
    coords.append({
        'lat': locations[0][lat_key],
        'lng': locations[0][lng_key],
        'address': locations[0]['original_address'],
        'type': 'depot',
        'index': 0
    })
    return coords

def generate_html_report():
    """Generate comprehensive HTML report of the simulation"""
    
    # Prepare route data for map
    map_routes = []
    try:
        with state_lock:
            for v_id in sorted(current_routes.keys()):
                route = current_routes[v_id]
                if route:
                    coords = generate_route_coordinates(route, all_locations)
                    map_routes.append({
                        'vehicle_id': v_id,
                        'coordinates': coords,
                        'color': ['#667eea', '#28a745', '#ffc107', '#dc3545'][v_id % 4]
                    })
    except Exception as e:
        print(f"Warning: Could not generate map routes: {e}")
        print(f"Sample location data: {all_locations[0] if all_locations else 'No locations'}")
        map_routes = []
    
    # Convert to JSON for JavaScript
    map_routes_json = json.dumps(map_routes)
    time_matrix_json = json.dumps(time_matrix)
    
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hybrid Delivery Simulation - Live Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .content {
            padding: 30px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }
        
        #map {
            width: 100%;
            height: 600px;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }
        
        .map-controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .vehicle-toggle {
            padding: 10px 20px;
            border: 2px solid #667eea;
            border-radius: 25px;
            background: white;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
        }
        
        .vehicle-toggle.active {
            background: #667eea;
            color: white;
        }
        
        .vehicle-toggle:hover {
            transform: scale(1.05);
        }
        
        .distance-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            margin-top: 20px;
            display: none;
        }
        
        .distance-info.active {
            display: block;
        }
        
        .distance-info h4 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .distance-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .distance-detail {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .distance-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        
        .distance-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        
        .timeline {
            position: relative;
            padding-left: 30px;
        }
        
        .timeline::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: linear-gradient(to bottom, #667eea, #764ba2);
        }
        
        .timeline-event {
            position: relative;
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .timeline-event::before {
            content: '';
            position: absolute;
            left: -36px;
            top: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #667eea;
            border: 3px solid white;
            box-shadow: 0 0 0 3px #667eea;
        }
        
        .event-time {
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
            margin-bottom: 8px;
        }
        
        .event-type {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .event-new-order {
            background: #ffd93d;
            color: #333;
        }
        
        .event-assignment {
            background: #6bcf7f;
            color: white;
        }
        
        .event-optimization {
            background: #667eea;
            color: white;
        }
        
        .event-rejected {
            background: #ff6b6b;
            color: white;
        }
        
        .event-details {
            color: #555;
            line-height: 1.6;
        }
        
        .vehicle-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .vehicle-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        }
        
        .vehicle-header {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255,255,255,0.3);
        }
        
        .route-stop {
            padding: 10px;
            margin: 8px 0;
            background: rgba(255,255,255,0.2);
            border-radius: 6px;
            font-size: 0.95em;
            cursor: pointer;
            transition: all 0.2s ease-in-out;
        }

        .route-stop:hover {
            background: rgba(255,255,255,0.4);
            transform: scale(1.02);
        }

        .route-stop.highlighted {
            background: #ffc107 !important; /* Yellow highlight */
            color: #333 !important;
            transform: scale(1.05);
            font-weight: bold;
        }
        
        .route-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }
        
        .metric {
            background: rgba(255,255,255,0.2);
            padding: 10px;
            border-radius: 6px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 1.4em;
            font-weight: bold;
        }
        
        .metric-label {
            font-size: 0.85em;
            opacity: 0.9;
        }
        
        .pending-orders {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .pending-orders h3 {
            color: #856404;
            margin-bottom: 15px;
        }
        
        .pending-order {
            background: white;
            padding: 12px;
            margin: 8px 0;
            border-radius: 6px;
            border-left: 4px solid #ffc107;
        }
        
        .premium-vehicle {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            padding: 25px;
            border-radius: 12px;
            color: white;
            margin-top: 20px;
        }
        
        .success-badge {
            background: #6bcf7f;
            color: white;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            display: inline-block;
        }
        
        .warning-badge {
            background: #ffc107;
            color: #333;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            display: inline-block;
        }
        
        .map-legend {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            margin: 8px 0;
        }
        
        .legend-icon {
            width: 30px;
            height: 30px;
            margin-right: 10px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        .legend-icon.depot {
            background: #dc3545;
            color: white;
            border-radius: 4px;
        }
        
        .legend-icon.stop {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚚 Hybrid Delivery Simulation Dashboard</h1>
            <p>Real-time Vehicle Routing with Layer 1 (Greedy) + Layer 2 (Optimization)</p>
            <p><strong>Simulation Period:</strong> {{start_time}} - {{end_time}}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Orders</div>
                <div class="stat-value">{{total_orders}}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Orders Assigned</div>
                <div class="stat-value">{{assigned_orders}}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Pending Orders</div>
                <div class="stat-value">{{pending_count}}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Active Vehicles</div>
                <div class="stat-value">{{active_vehicles}}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Layer 2 Optimizations</div>
                <div class="stat-value">{{optimization_count}}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg Route Duration</div>
                <div class="stat-value">{{avg_duration}} min</div>
            </div>
        </div>
        
        <div class="content">
            {{pending_orders_section}}
            
            <div class="section">
                <h2 class="section-title">🗺️ Interactive Route Map</h2>
                
                <div class="map-legend">
                    <div class="legend-item">
                        <div class="legend-icon depot">D</div>
                        <span>Depot (Start/End Point)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-icon stop">●</div>
                        <span>Delivery Stop</span>
                    </div>
                </div>
                
                <div class="map-controls" id="vehicleToggles"></div>
                
                <div id="map"></div>
                
                <div class="distance-info" id="distanceInfo">
                    <h4>📍 Route Segment Information</h4>
                    <p id="segmentDescription">Select two consecutive stops on a route to see travel details.</p>
                    <div class="distance-details" id="distanceDetails"></div>
                </div>
            </div>
            
            <div class="section">
                <h2 class="section-title">Final Fleet Status</h2>
                <div class="vehicle-grid">
                    {{vehicle_cards}}
                </div>
            </div>
            
            {{premium_section}}
            
            <div class="section">
                <h2 class="section-title">Simulation Timeline</h2>
                <div class="timeline">
                    {{timeline_events}}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Route data from Python
        const routesData = {{map_routes_json}};
        const timeMatrix = {{time_matrix_json}};
        
        let map;
        let directionsService;
        let directionsRenderers = [];
        let markers = [];
        let activeRoutes = new Set();
        let selectedMarkers = [];

        // --- NEW --- Variables for interactive highlighting
        let mapMarkers = {};
        let highlightRenderer = null;
        let activeHighlightVehicle = null;
        let selectedStopIndices = [];
        
        function initMap() {
            // Initialize map centered on depot
            const depotLocation = routesData.length > 0 && routesData[0].coordinates.length > 0
                ? { lat: routesData[0].coordinates[0].lat, lng: routesData[0].coordinates[0].lng }
                : { lat: 22.7196, lng: 75.8577 }; // Default to Indore
            
            map = new google.maps.Map(document.getElementById('map'), {
                zoom: 12,
                center: depotLocation,
                mapTypeControl: true,
                streetViewControl: false,
                fullscreenControl: true
            });
            
            directionsService = new google.maps.DirectionsService();

            // --- NEW --- Initialize data structures for highlighting
            routesData.forEach(route => {
                mapMarkers[route.vehicle_id] = [];
            });
            
            // Create vehicle toggle buttons
            const toggleContainer = document.getElementById('vehicleToggles');
            routesData.forEach((route, idx) => {
                const button = document.createElement('button');
                button.className = 'vehicle-toggle active';
                button.textContent = `Vehicle ${route.vehicle_id}`;
                button.style.borderColor = route.color;
                button.onclick = () => toggleRoute(route.vehicle_id, button);
                toggleContainer.appendChild(button);
                activeRoutes.add(route.vehicle_id);
            });
            
            // Display all routes initially
            routesData.forEach(route => {
                displayRoute(route);
            });
        }
        
        function toggleRoute(vehicleId, button) {
            if (activeRoutes.has(vehicleId)) {
                activeRoutes.delete(vehicleId);
                button.classList.remove('active');
            } else {
                activeRoutes.add(vehicleId);
                button.classList.add('active');
            }
            
            // Clear and redraw
            clearMap();
            routesData.forEach(route => {
                if (activeRoutes.has(route.vehicle_id)) {
                    displayRoute(route);
                }
            });
        }
        
        function displayRoute(routeData) {
            const coords = routeData.coordinates;
            if (coords.length < 2) return;
            
            // Create waypoints for Google Directions API
            const origin = { lat: coords[0].lat, lng: coords[0].lng };
            const destination = { lat: coords[coords.length - 1].lat, lng: coords[coords.length - 1].lng };
            const waypoints = coords.slice(1, -1).map(coord => ({
                location: { lat: coord.lat, lng: coord.lng },
                stopover: true
            }));
            
            const directionsRenderer = new google.maps.DirectionsRenderer({
                map: map,
                suppressMarkers: true,
                polylineOptions: {
                    strokeColor: routeData.color,
                    strokeWeight: 5,
                    strokeOpacity: 0.7
                }
            });
            
            const request = {
                origin: origin,
                destination: destination,
                waypoints: waypoints,
                travelMode: google.maps.TravelMode.DRIVING,
                optimizeWaypoints: false
            };
            
            directionsService.route(request, (result, status) => {
                if (status === 'OK') {
                    directionsRenderer.setDirections(result);
                } else {
                    console.error('Directions request failed:', status);
                    drawSimplePolyline(coords, routeData.color);
                }
            });
            
            directionsRenderers.push(directionsRenderer);
            
            // Add markers for each stop
            coords.forEach((coord, idx) => {
                const isDepot = coord.type === 'depot';
                
                // --- MODIFIED --- Enhanced marker styles for better visibility
                const markerIcon = {
                    path: isDepot ? google.maps.SymbolPath.FORWARD_CLOSED_ARROW : google.maps.SymbolPath.CIRCLE,
                    rotation: isDepot ? -90 : 0, // Makes the depot a square
                    fillColor: isDepot ? '#dc3545' : routeData.color,
                    fillOpacity: 1,
                    strokeColor: 'white',
                    strokeWeight: 2.5,
                    scale: isDepot ? 9 : 10 // Increased scale for stops
                };

                const marker = new google.maps.Marker({
                    position: { lat: coord.lat, lng: coord.lng },
                    map: map,
                    title: coord.address,
                    icon: markerIcon,
                    label: { // Using a label object for better styling
                        text: isDepot ? 'D' : (idx).toString(),
                        color: 'white',
                        fontSize: '11px',
                        fontWeight: 'bold'
                    }
                });
                
                // --- NEW --- Store marker for highlighting interactivity
                mapMarkers[routeData.vehicle_id][idx] = { marker, coord };

                const infoWindow = new google.maps.InfoWindow({
                    content: `
                        <div style="padding: 10px;">
                            <strong>${isDepot ? 'Depot' : 'Stop ' + idx}</strong><br>
                            ${coord.address}<br>
                            <small>Vehicle ${routeData.vehicle_id}</small>
                        </div>
                    `
                });
                
                marker.addListener('click', () => {
                    infoWindow.open(map, marker);
                    handleMarkerClick(marker, coord, routeData);
                });
                
                markers.push({ marker, coord, routeData });
            });
        }
        
        function drawSimplePolyline(coords, color) {
            const path = coords.map(c => ({ lat: c.lat, lng: c.lng }));
            const polyline = new google.maps.Polyline({
                path: path,
                strokeColor: color,
                strokeWeight: 4,
                strokeOpacity: 0.7,
                map: map
            });
        }
        
        function handleMarkerClick(marker, coord, routeData) {
            if (selectedMarkers.length === 2) {
                selectedMarkers = [];
            }
            
            selectedMarkers.push({ marker, coord, routeData });
            
            if (selectedMarkers.length === 2) {
                calculateSegmentInfo();
            }
        }
        
        function calculateSegmentInfo() {
            const [first, second] = selectedMarkers;
            
            if (first.routeData.vehicle_id !== second.routeData.vehicle_id) {
                document.getElementById('segmentDescription').textContent = 
                    'Please select two stops from the same vehicle route.';
                return;
            }
            
            const route = first.routeData.coordinates;
            const firstIdx = route.findIndex(c => 
                c.lat === first.coord.lat && c.lng === first.coord.lng
            );
            const secondIdx = route.findIndex(c => 
                c.lat === second.coord.lat && c.lng === second.coord.lng
            );
            
            if (firstIdx === -1 || secondIdx === -1) return;
            
            const travelTime = timeMatrix[first.coord.index][second.coord.index];
            const distance = calculateDistance(
                first.coord.lat, first.coord.lng,
                second.coord.lat, second.coord.lng
            );
            
            const distanceInfo = document.getElementById('distanceInfo');
            const distanceDetails = document.getElementById('distanceDetails');
            
            document.getElementById('segmentDescription').textContent = 
                `Route segment from ${first.coord.address.split(',')[0]} to ${second.coord.address.split(',')[0]}`;
            
            distanceDetails.innerHTML = `
                <div class="distance-detail">
                    <div class="distance-label">Travel Time</div>
                    <div class="distance-value">${travelTime.toFixed(1)} min</div>
                </div>
                <div class="distance-detail">
                    <div class="distance-label">Distance</div>
                    <div class="distance-value">${distance.toFixed(1)} km</div>
                </div>
                <div class="distance-detail">
                    <div class="distance-label">Vehicle</div>
                    <div class="distance-value">${first.routeData.vehicle_id}</div>
                </div>
                <div class="distance-detail">
                    <div class="distance-label">Avg Speed</div>
                    <div class="distance-value">${(distance / (travelTime / 60)).toFixed(1)} km/h</div>
                </div>
            `;
            
            distanceInfo.classList.add('active');
        }
        
        function calculateDistance(lat1, lon1, lat2, lon2) {
            const R = 6371; // Earth's radius in km
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                    Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            return R * c;
        }
        
        function clearMap() {
            directionsRenderers.forEach(renderer => renderer.setMap(null));
            markers.forEach(m => m.marker.setMap(null));
            directionsRenderers = [];
            markers = [];
            selectedMarkers = [];
            document.getElementById('distanceInfo').classList.remove('active');
        }

        // --- NEW --- Functions for interactive highlighting
        function highlightStop(element, vehicleId, routeIndex) {
            if (vehicleId !== activeHighlightVehicle) {
                // Switched to a new vehicle, so reset everything
                document.querySelectorAll('.route-stop.highlighted').forEach(el => {
                    el.classList.remove('highlighted');
                });
                selectedStopIndices = [];
                activeHighlightVehicle = vehicleId;
            }

            // Toggle selection for the current stop
            const selectionIndex = selectedStopIndices.indexOf(routeIndex);
            if (selectionIndex > -1) {
                selectedStopIndices.splice(selectionIndex, 1);
                element.classList.remove('highlighted');
            } else {
                selectedStopIndices.push(routeIndex);
                element.classList.add('highlighted');
            }
            
            updateHighlightPath();
        }

        function updateHighlightPath() {
            // 1. Clear previous highlights
            if (highlightRenderer) {
                highlightRenderer.setMap(null);
                highlightRenderer = null;
            }
            for (const vId in mapMarkers) {
                mapMarkers[vId].forEach(m => m.marker.setAnimation(null));
            }

            if (selectedStopIndices.length === 0 || activeHighlightVehicle === null) {
                return; // Nothing to highlight
            }

            // 2. Animate selected markers
            selectedStopIndices.forEach(idx => {
                if (mapMarkers[activeHighlightVehicle] && mapMarkers[activeHighlightVehicle][idx]) {
                    mapMarkers[activeHighlightVehicle][idx].marker.setAnimation(google.maps.Animation.BOUNCE);
                }
            });

            // 3. Draw the highlighted path up to the furthest selected stop
            const routeData = routesData.find(r => r.vehicle_id === activeHighlightVehicle);
            if (!routeData) return;

            const lastStopIndex = Math.max(...selectedStopIndices);
            const highlightCoords = routeData.coordinates.slice(0, lastStopIndex + 1);

            if (highlightCoords.length < 2) return;

            const origin = { lat: highlightCoords[0].lat, lng: highlightCoords[0].lng };
            const destination = { lat: highlightCoords[highlightCoords.length - 1].lat, lng: highlightCoords[highlightCoords.length - 1].lng };
            const waypoints = highlightCoords.slice(1, -1).map(c => ({
                location: { lat: c.lat, lng: c.lng },
                stopover: true
            }));
            
            highlightRenderer = new google.maps.DirectionsRenderer({
                map: map,
                suppressMarkers: true,
                preserveViewport: true, // Don't zoom/pan the map
                polylineOptions: {
                    strokeColor: '#e74c3c', // Bright red highlight
                    strokeWeight: 8,
                    strokeOpacity: 0.9,
                    zIndex: 99
                }
            });

            const request = {
                origin: origin,
                destination: destination,
                waypoints: waypoints,
                travelMode: google.maps.TravelMode.DRIVING,
                optimizeWaypoints: false
            };

            directionsService.route(request, (result, status) => {
                if (status === 'OK') {
                    highlightRenderer.setDirections(result);
                } else {
                    console.error('Highlight directions request failed:', status);
                }
            });
        }
    </script>
    
    <script async defer
        src="https://maps.googleapis.com/maps/api/js?key={{google_api_key}}&callback=initMap">
    </script>
</body>
</html>
"""
    
    # Calculate statistics
    total_orders = len([e for e in simulation_events if e['type'] == 'new_order'])
    assigned_orders = len([e for e in simulation_events if e['type'] == 'assignment' and e.get('success')])
    optimization_count = len([e for e in simulation_events if e['type'] == 'optimization'])
    pending_count = len(pending_orders)
    
    with state_lock:
        active_vehicles = len([r for r in current_routes.values() if r])
        avg_duration = 0
        if active_vehicles > 0:
            total_duration = sum([calculate_route_cost(r, time_matrix) for r in current_routes.values() if r])
            avg_duration = int(total_duration / active_vehicles) if total_duration > 0 else 0
    
    # Generate pending orders section
    pending_section = ""
    if pending_orders:
        pending_html = f"""
        <div class="pending-orders">
            <h3>⚠️ Pending Orders (End of Day)</h3>
            <p>The following orders could not be assigned to the standard fleet:</p>
        """
        for order in pending_orders:
            order_loc = all_locations[order['index']]['original_address'].split(',')[0]
            pending_html += f"""
            <div class="pending-order">
                <strong>Order #{order['id']}</strong> - {order_loc}
            </div>
            """
        pending_html += "</div>"
        pending_section = pending_html
    
    # Generate vehicle cards
    vehicle_cards_html = ""
    with state_lock:
        for v_id in sorted(current_routes.keys()):
            route = current_routes[v_id]
            if route:
                route_cost = calculate_route_cost(route, time_matrix)
                stops_html = ""
                for idx, stop in enumerate(route, 1):
                    loc_name = all_locations[stop]['original_address'].split(',')[0]
                    # --- MODIFIED --- Added onclick attribute for interactivity
                    stops_html += f"""
                    <div class="route-stop" 
                         onclick="highlightStop(this, {v_id}, {idx})">
                        {idx}. {loc_name}
                    </div>
                    """
                
                vehicle_cards_html += f"""
                <div class="vehicle-card">
                    <div class="vehicle-header">Vehicle {v_id}</div>
                    {stops_html}
                    <div class="route-metrics">
                        <div class="metric">
                            <div class="metric-value">{len(route)}</div>
                            <div class="metric-label">Stops</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{route_cost:.0f}</div>
                            <div class="metric-label">Minutes</div>
                        </div>
                    </div>
                </div>
                """
            else:
                vehicle_cards_html += f"""
                <div class="vehicle-card">
                    <div class="vehicle-header">Vehicle {v_id}</div>
                    <p style="text-align: center; opacity: 0.7; padding: 20px;">No route assigned</p>
                </div>
                """
    
    # Generate premium vehicle section
    premium_section = ""
    premium_event = next((e for e in reversed(simulation_events) if e['type'] == 'premium'), None)
    if premium_event:
        premium_section = f"""
        <div class="section">
            <h2 class="section-title">Premium Vehicle Deployment</h2>
            <div class="premium-vehicle">
                <h3>🌟 Premium Vehicle Route</h3>
                <p><strong>Stops:</strong> {premium_event['stops']}</p>
                <p><strong>Duration:</strong> {premium_event['duration']:.2f} minutes</p>
                <p><strong>Route:</strong> {premium_event['route']}</p>
            </div>
        </div>
        """
    
    # Generate timeline
    timeline_html = ""
    for event in simulation_events:
        event_type_class = f"event-{event['type'].replace('_', '-')}"
        event_type_label = event['type'].replace('_', ' ').title()
        
        timeline_html += f"""
        <div class="timeline-event">
            <div class="event-time">{event['time']}</div>
            <span class="event-type {event_type_class}">{event_type_label}</span>
            <div class="event-details">{event['description']}</div>
        </div>
        """
    
    # Fill in template
    html_content = html_template.replace('{{start_time}}', format_time(0))
    html_content = html_content.replace('{{end_time}}', format_time((SIMULATION_END_HOUR - SIMULATION_START_HOUR) * 60))
    html_content = html_content.replace('{{total_orders}}', str(total_orders))
    html_content = html_content.replace('{{assigned_orders}}', str(assigned_orders))
    html_content = html_content.replace('{{pending_count}}', str(pending_count))
    html_content = html_content.replace('{{active_vehicles}}', str(active_vehicles))
    html_content = html_content.replace('{{optimization_count}}', str(optimization_count))
    html_content = html_content.replace('{{avg_duration}}', str(avg_duration))
    html_content = html_content.replace('{{pending_orders_section}}', pending_section)
    html_content = html_content.replace('{{vehicle_cards}}', vehicle_cards_html)
    html_content = html_content.replace('{{premium_section}}', premium_section)
    html_content = html_content.replace('{{timeline_events}}', timeline_html)
    html_content = html_content.replace('{{map_routes_json}}', map_routes_json)
    html_content = html_content.replace('{{time_matrix_json}}', time_matrix_json)
    html_content = html_content.replace('{{google_api_key}}', GOOGLE_MAPS_API_KEY)
    
    with open(OUTPUT_HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ HTML Dashboard saved to '{OUTPUT_HTML_FILE}'")
    
    # Auto-open in browser
    import webbrowser
    import os
    try:
        filepath = os.path.abspath(OUTPUT_HTML_FILE)
        webbrowser.open(f"file://{filepath}")
        print("📊 Dashboard opened in your default web browser.")
    except Exception as e:
        print(f"Could not auto-open dashboard. Please open '{OUTPUT_HTML_FILE}' manually.")

# --- Layer 2 Worker Thread ---
def layer2_worker(time_matrix):
    global current_routes, simulation_events
    while simulation_running:
        time.sleep(LAYER_2_INTERVAL_SECONDS)
        with state_lock:
            routes_to_optimize = {vid: r[:] for vid, r in current_routes.items()}
        
        optimized_routes = batch_optimization_vrp(
            routes_to_optimize, time_matrix, NUM_VEHICLES,
            MAX_STOPS_PER_ROUTE, MAX_ROUTE_DURATION_MINS
        )
        
        with state_lock:
            current_routes = optimized_routes
            current_time = len([e for e in simulation_events if e['type'] in ['new_order', 'assignment']]) * MINUTES_PER_TICK
            
            simulation_events.append({
                'type': 'optimization',
                'time': format_time(current_time),
                'description': f"Layer 2 optimization completed. Fleet routes reoptimized for efficiency."
            })
            
            print("\n--- FLEET STATUS (Updated by Layer 2) ---")
            for v_id, route in sorted(current_routes.items()):
                if route:
                    route_str = ' -> '.join([all_locations[i]['original_address'].split(',')[0] for i in route])
                    print(f"Vehicle {v_id} (Stops: {len(route)}): Depot -> {route_str} -> Depot")

# --- Main Simulation Function ---
def run_hybrid_simulation():
    global current_routes, pending_orders, simulation_running, all_locations, time_matrix, simulation_events

    print("--- Starting HYBRID DYNAMIC Delivery Simulation with Live Dashboard ---")
    
    try:
        with open(TIME_MATRIX_FILE, 'r') as f: 
            data = json.load(f)
        all_locations, time_matrix = data['locations'], data['time_matrix']
        print(f"✅ Master time matrix and {len(all_locations)} locations loaded successfully.")
    except FileNotFoundError:
        print(f"Error: '{TIME_MATRIX_FILE}' not found. Run 'build_master_matrix.py' first.")
        return

    current_routes = {i: [] for i in range(NUM_VEHICLES)}
    order_counter = 0
    simulation_events = []

    layer2_thread = threading.Thread(target=layer2_worker, args=(time_matrix,), daemon=True)
    layer2_thread.start()
    print("✅ Layer 2 background optimization thread started.")

    # --- Main Simulation Loop (Layer 1) ---
    for minute in range(SIMULATION_START_HOUR * 60, SIMULATION_END_HOUR * 60, MINUTES_PER_TICK):
        current_time_str = f"Day 1, {minute//60:02d}:{minute%60:02d}"
        print(f"\n{'='*15} {current_time_str} {'='*15}")
        
        if random.random() < PROBABILITY_OF_NEW_ORDER_PER_TICK:
            order_counter += 1
            new_order_idx = random.randint(1, len(all_locations) - 1)
            pending_orders.append({'id': order_counter, 'index': new_order_idx})
            order_location = all_locations[new_order_idx]['original_address'].split(',')[0]
            
            print(f"EVENT: New order #{order_counter} received for {order_location}.")
            print(f"Total pending orders: {len(pending_orders)}")
            
            simulation_events.append({
                'type': 'new_order',
                'time': format_time(minute - SIMULATION_START_HOUR * 60),
                'description': f"<strong>Order #{order_counter}</strong> received for delivery to <strong>{order_location}</strong>"
            })

        if pending_orders:
            assigned_this_tick = False
            for order_to_assign in pending_orders[:]:
                print(f"\nAttempting to assign Order #{order_to_assign['id']}...")
                
                with state_lock:
                    final_routes, method = assign_new_order_realtime(
                        order_to_assign['index'], current_routes, time_matrix,
                        NUM_VEHICLES, MAX_STOPS_PER_ROUTE, MAX_ROUTE_DURATION_MINS
                    )

                if final_routes:
                    order_location = all_locations[order_to_assign['index']]['original_address'].split(',')[0]
                    print(f"SUCCESS: Order #{order_to_assign['id']} assigned via {method} method.")
                    
                    with state_lock:
                        current_routes = final_routes
                    
                    simulation_events.append({
                        'type': 'assignment',
                        'time': format_time(minute - SIMULATION_START_HOUR * 60),
                        'description': f"<span class='success-badge'>✓ ASSIGNED</span> Order #{order_to_assign['id']} to fleet using <strong>{method}</strong> method. Destination: {order_location}",
                        'success': True
                    })
                    
                    pending_orders.remove(order_to_assign)
                    assigned_this_tick = True
                    break
            
            if assigned_this_tick:
                with state_lock:
                    print("\n--- CURRENT FLEET STATUS ---")
                    for v_id, route in sorted(current_routes.items()):
                        if route:
                            route_str = ' -> '.join([all_locations[i]['original_address'].split(',')[0] for i in route])
                            print(f"Vehicle {v_id} (Stops: {len(route)}): Depot -> {route_str} -> Depot")
            else:
                print("\nINFO: No pending orders could be assigned in this time tick.")
        
        time.sleep(0.5)

    # --- End of Day Processing ---
    simulation_running = False
    print("\n--- Dynamic Simulation Ended ---")
    time.sleep(LAYER_2_INTERVAL_SECONDS + 2)
    
    if pending_orders:
        print("\n--- Deploying PREMIUM Vehicle for remaining orders ---")
        premium_route = []
        while pending_orders:
            order = pending_orders.pop(0)
            premium_route.append(order['index'])
        premium_cost = calculate_route_cost(premium_route, time_matrix)
        route_str = ' -> '.join([all_locations[i]['original_address'].split(',')[0] for i in premium_route])
        print(f"Premium Vehicle Route (Stops: {len(premium_route)}): Depot -> {route_str} -> Depot")
        print(f"Premium Route Duration: {premium_cost:.2f} mins.")
        
        simulation_events.append({
            'type': 'premium',
            'time': format_time((SIMULATION_END_HOUR - SIMULATION_START_HOUR) * 60),
            'description': f"<span class='warning-badge'>PREMIUM DEPLOYMENT</span> Premium vehicle dispatched for {len(premium_route)} remaining orders.",
            'stops': len(premium_route),
            'duration': premium_cost,
            'route': route_str
        })
    else:
        print("All orders were assigned to the standard fleet.")
    
    # Generate final HTML report
    print("\n--- Generating HTML Dashboard ---")
    generate_html_report()

if __name__ == "__main__":
    run_hybrid_simulation()