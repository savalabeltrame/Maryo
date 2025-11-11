let map = L.map('map').setView([-34.6037, -58.3816], 13); // Buenos Aires default

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap'
}).addTo(map);

// marcador del usuario
let usuarioMarker = null;

// intentamos geolocalizar
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(position => {
        let lat = position.coords.latitude;
        let lng = position.coords.longitude;
        map.setView([lat, lng], 15);
        usuarioMarker = L.marker([lat, lng]).addTo(map).bindPopup("Tú estás aquí").openPopup();
    });
}

// Mostrar conductores simulados
fetch("/api/drivers_nearby").then(r => r.json()).then(data => {
    data.forEach(driver => {
        L.marker([driver.lat, driver.lng]).addTo(map)
            .bindPopup(driver.name + " (conductor)");
    });
});

// acción botón (solo demo)
function pedirTaxi() {
    document.getElementById("estado").innerHTML = "¡Taxi solicitado! Espere confirmación del conductor... (DEMO)";
}
