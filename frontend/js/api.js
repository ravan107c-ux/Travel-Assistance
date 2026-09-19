const API_URL = "http://127.0.0.1:8000";


async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`${API_URL}${endpoint}`, {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
        ...options,
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return response.json();
}


async function getDashboard() {
    return apiRequest("/api/dashboard/");
}


async function getBus(busNumber) {
    return apiRequest(`/api/buses/${encodeURIComponent(busNumber)}`);
}


async function getETA(routeNumber, stopName) {
    return apiRequest(
        `/api/routes/${encodeURIComponent(routeNumber)}/eta?stop_name=${encodeURIComponent(stopName)}`
    );
}


async function compareRouteOptions(fromStop, toStop) {
    return apiRequest(
        `/api/routes/compare?from_stop=${encodeURIComponent(fromStop)}&to_stop=${encodeURIComponent(toStop)}`
    );
}


async function getTracking(routeNumber = "21B") {
    return apiRequest(`/api/routes/${encodeURIComponent(routeNumber)}/tracking`);
}


async function getCrowd(routeNumber) {
    return apiRequest(`/api/crowd/${encodeURIComponent(routeNumber)}`);
}


async function getAlerts() {
    return apiRequest("/api/alerts/");
}


async function getDeparture(requiredArrival = "09:00") {
    return apiRequest(
        `/api/departure/?required_arrival=${encodeURIComponent(requiredArrival)}`
    );
}


async function sendChat(message, language = "English") {
    return apiRequest("/api/chat/", {
        method: "POST",
        body: JSON.stringify({ message, language }),
    });
}
