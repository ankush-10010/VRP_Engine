import React, { useMemo, useEffect, useState } from 'react';
import { GoogleMap, Polyline, Marker, InfoWindow, useJsApiLoader, DirectionsRenderer } from '@react-google-maps/api';
import type { VehicleRoute } from '../api/api';

const containerStyle = {
    width: '100%',
    height: '100%',
    minHeight: '400px',
    borderRadius: '12px'
};

const defaultCenter = {
    lat: 28.6139,
    lng: 77.2090
};

// Vibrant colors for routes
const ROUTE_COLORS = [
    '#FF5733', '#33FF57', '#3357FF', '#FF33A8', '#33FFF5',
    '#F5FF33', '#800000', '#008080', '#800080', '#FF8C00'
];

interface Props {
    routes: VehicleRoute[];
}

const ResultsMap: React.FC<Props> = ({ routes }) => {
    const { isLoaded } = useJsApiLoader({
        id: 'google-map-script',
        googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''
    });

    const [selectedStop, setSelectedStop] = useState<any>(null);
    const [directions, setDirections] = useState<Record<string, google.maps.DirectionsResult[] | null>>({});

    // Fetch directions
    useEffect(() => {
        if (!isLoaded || routes.length === 0) return;
        
        const fetchDirections = async () => {
            const directionsService = new window.google.maps.DirectionsService();
            const newDirections: Record<string, google.maps.DirectionsResult[] | null> = {};

            // Fetch directions for each route
            for (const route of routes) {
                const path = route.steps
                    .filter(s => s.lat && s.lng)
                    .map(step => ({ lat: step.lat!, lng: step.lng! }));

                if (path.length >= 2) {
                    const chunks: any[] = [];
                    // Chunk into overlapping segments of 25 stops (origin + dest + 23 waypoints)
                    for (let i = 0; i < path.length - 1; i += 24) {
                        const segment = path.slice(i, i + 25);
                        const origin = segment[0];
                        const destination = segment[segment.length - 1];
                        const waypoints = segment.slice(1, -1).map(p => ({ location: p, stopover: true }));
                        chunks.push({ origin, destination, waypoints });
                    }

                    try {
                        const results: google.maps.DirectionsResult[] = [];
                        for (const chunk of chunks) {
                            const result = await directionsService.route({
                                origin: chunk.origin,
                                destination: chunk.destination,
                                waypoints: chunk.waypoints,
                                travelMode: window.google.maps.TravelMode.DRIVING,
                            });
                            results.push(result);
                            // Add a small delay to avoid OVER_QUERY_LIMIT
                            await new Promise(resolve => setTimeout(resolve, 200));
                        }
                        newDirections[route.vehicle_id] = results;
                    } catch (error) {
                        console.error("Directions request failed for route", route.vehicle_id, error);
                        newDirections[route.vehicle_id] = null; // Fallback to Polyline
                    }
                } else {
                    newDirections[route.vehicle_id] = null;
                }
            }
            setDirections(newDirections);
        };
        
        fetchDirections();
    }, [isLoaded, routes]);

    const mapCenter = useMemo(() => {
        if (routes.length > 0 && routes[0].steps.length > 0) {
            // Center on the first stop of the first route
            const firstStep = routes[0].steps[0];
            if (firstStep.lat && firstStep.lng) {
                return { lat: firstStep.lat, lng: firstStep.lng };
            }
        }
        return defaultCenter;
    }, [routes]);

    const renderRoutes = () => {
        return routes.map((route, index) => {
            const path = route.steps
                .filter(s => s.lat && s.lng) // Filter out missing coords
                .map(step => ({ lat: step.lat!, lng: step.lng! }));

            const color = ROUTE_COLORS[route.vehicle_id % ROUTE_COLORS.length];

            return (
                <React.Fragment key={route.vehicle_id}>
                    {/* Route Path */}
                    {directions[route.vehicle_id] !== undefined ? (
                        directions[route.vehicle_id] !== null ? (
                            directions[route.vehicle_id]!.map((dirResult, chunkIdx) => (
                                <DirectionsRenderer
                                    key={`${route.vehicle_id}-chunk-${chunkIdx}`}
                                    directions={dirResult}
                                    options={{
                                        polylineOptions: {
                                            strokeColor: color,
                                            strokeOpacity: 0.8,
                                            strokeWeight: 4,
                                        },
                                        suppressMarkers: true // We draw our own custom markers
                                    }}
                                />
                            ))
                        ) : (
                            <Polyline
                                path={path}
                                options={{
                                    strokeColor: color,
                                    strokeOpacity: 0.8,
                                    strokeWeight: 4,
                                }}
                            />
                        )
                    ) : null}

                    {/* Stops */}
                    {route.steps.map((step, stepIndex) => (
                        step.lat && step.lng && (
                            <Marker
                                key={`${route.vehicle_id}-${stepIndex}`}
                                position={{ lat: step.lat, lng: step.lng }}
                                label={{
                                    text: `${stepIndex}`,
                                    color: 'white',
                                    fontWeight: 'bold'
                                }}
                                onClick={() => setSelectedStop({ ...step, vehicleId: route.vehicle_id })}
                                icon={stepIndex === 0 ? undefined : {
                                    path: window.google.maps.SymbolPath.CIRCLE,
                                    scale: 10,
                                    fillColor: color,
                                    fillOpacity: 1,
                                    strokeWeight: 2,
                                    strokeColor: 'white',
                                }}
                            />
                        )
                    ))}
                </React.Fragment>
            );
        });
    };

    if (!isLoaded) return <div>Loading Map...</div>;

    return (
        <GoogleMap
            mapContainerStyle={containerStyle}
            center={mapCenter}
            zoom={11}
        >
            {renderRoutes()}

            {selectedStop && (
                <InfoWindow
                    position={{ lat: selectedStop.lat, lng: selectedStop.lng }}
                    onCloseClick={() => setSelectedStop(null)}
                >
                    <div style={{ padding: '5px' }}>
                        <h4 style={{ margin: '0 0 5px 0' }}>Stop #{selectedStop.stop_index}</h4>
                        <p style={{ margin: 0 }}><strong>Vehicle:</strong> {selectedStop.vehicleId}</p>
                        <p style={{ margin: 0 }}><strong>Address:</strong> {selectedStop.address}</p>
                        <p style={{ margin: 0 }}><strong>Arrival:</strong> {selectedStop.arrival_time_min.toFixed(0)} min</p>
                    </div>
                </InfoWindow>
            )}
        </GoogleMap>
    );
};

export default React.memo(ResultsMap);
