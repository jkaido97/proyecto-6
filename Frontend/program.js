let map = L.map('map').setView([4.6097, -74.0817], 14);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

let capaMapa;

async function call_API(accion) {
    const urls = {
        map: "http://127.0.0.1:8000/btn_Map",
        mapveterinaria: "http://127.0.0.1:8000/btn_Mapveterinaria",
        distancia: "http://127.0.0.1:8000/info_distancia",
        costos: "http://127.0.0.1:8000/info_costos",
        numemergencia: "http://127.0.0.1:8000/info_numemergencia",
        lista: "http://127.0.0.1:8000/est_lista",
        analizar: "http://127.0.0.1:8000/analizar"
    };

    let urlAPI = urls[accion];

    try {
        const response = await fetch(urlAPI);
        const data = await response.json();
        console.log(data);

        const infoPanel = document.getElementById('info-panel');
        const infoContent = document.getElementById('info-content');

        // Si es el mapa del barrio
        if (accion === "map") {
            if (capaMapa) {
                map.removeLayer(capaMapa);
            }
            
            // Dibujar el barrio con borde resaltado
            capaMapa = L.geoJSON(data, {
                style: {
                    color: '#FF0000',        // Color del borde (rojo)
                    weight: 3,               // Grosor del borde
                    opacity: 0.8,            // Opacidad del borde
                    fillColor: '#FFFF00',    // Color de relleno (amarillo)
                    fillOpacity: 0.3         // Opacidad del relleno
                }
            }).addTo(map);
            
            // Ajustar el zoom para que se vea La Candelaria
            if (capaMapa.getLayers().length > 0) {
                map.fitBounds(capaMapa.getBounds());
            }
        }
        
        
        else if (accion === "mapveterinaria") {
            if (capaMapa) {
                map.removeLayer(capaMapa);
            }
            
            
            capaMapa = L.geoJSON(data, {
                pointToLayer: function (feature, latlng) {
                    return L.circleMarker(latlng, {
                        radius: 6,
                        fillColor: "#0066CC",
                        color: "#fff",
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    });
                },
                onEachFeature: function (feature, layer) {
                    if (feature.properties) {
                        let popupContent = "<b>veterinaria</b><br>";
                        for (let [key, value] of Object.entries(feature.properties)) {
                            popupContent += `${key}: ${value}<br>`;
                        }
                        layer.bindPopup(popupContent);
                    }
                }
            }).addTo(map);

            // Ajustar el zoom automático
            if (capaMapa.getLayers().length > 0) {
                map.fitBounds(capaMapa.getBounds());
            }
        }
        
        else {
            // Mostrar información alfabética y tabular en el panel lateral
            infoPanel.classList.remove('hidden');
            if (accion === "distancia") {
                infoContent.innerHTML = `<h3>Columnas Localidades</h3><ul>${data.columnas.map(col => `<li>${col}</li>`).join('')}</ul>`;
            } else if (accion === "costos") {
                infoContent.innerHTML = `<h3>Costos de Veterinarias</h3><p><b>${data.costos.toFixed(2)}</b> USD</p>`;
            } else if (accion === "numemergencia") {
                infoContent.innerHTML = `<h3>Número de Emergencia</h3><p><b>${data.numemergencia}</b></p>`;
            } else if (accion === "analizar") {
                infoContent.innerHTML = `<h3>Análisis de Paradas</h3><p>Total de paradas de SITP en La Candelaria: <b>${data.total_paradas}</b></p>`;
            } else if (accion === "lista") {
                let html = "<h3>20 Veterinarias</h3><ul>";
                data.forEach(est => {
                    const nombre = est['Nombre_del'] || est['nombre'] || 'Sin Nombre';
                    const cenefa = est['Cenefa'] || est['cenefa'] || 'N/A';
                    html += `<li><b>${cenefa}</b>: ${nombre}</li>`;
                });
                html += "</ul>";
                infoContent.innerHTML = html;
            }
        }

    } catch (error) {
        console.error("Error al llamar a la API: ", error);
    }
}

// Event listeners corregidos
document.getElementById("btn_Map").onclick = () => call_API("map");
document.getElementById("btn_MapSITP").onclick = () => call_API("mapsitp");
document.getElementById("info_distancia").onclick = () => call_API("distancia");
document.getElementById("info_costos").onclick = () => call_API("costos");
document.getElementById("info_numemergencia").onclick = () => call_API("numemergencia");
document.getElementById("est_lista").onclick = () => call_API("lista");
document.getElementById("analizar").onclick = () => call_API("analizar");