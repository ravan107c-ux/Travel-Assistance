async function loadDashboard() {

    try {

        const data =
            await getDashboard();

        const trackedBuses = document.getElementById("trackedBuses");
        const avgDelay = document.getElementById("avgDelay");
        const crowdLevel = document.getElementById("crowdLevel");
        const activeAlerts = document.getElementById("activeAlerts");

        if (trackedBuses) trackedBuses.textContent = data.tracked_buses;
        if (avgDelay) avgDelay.textContent = `${data.average_delay} min`;
        if (crowdLevel) crowdLevel.textContent = data.crowd_level;
        if (activeAlerts) activeAlerts.textContent = data.active_alerts;

    } catch (error) {

        console.error(
            "Dashboard error:",
            error
        );
    }
}

document.addEventListener(
    "DOMContentLoaded",
    loadDashboard
);