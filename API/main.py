"""
main.py - API REST de Veterinarias en Bogotá
Endpoints:
  GET  /                          -> salud de la API
  GET  /localidades               -> lista de localidades de Bogotá
  GET  /localidad-por-punto       -> detecta localidad desde lat/lon
  GET  /veterinarias              -> todas las veterinarias
  GET  /veterinarias/buscar       -> buscar por radio desde un punto
  GET  /veterinarias/{id}         -> detalle de una veterinaria
  GET  /estadisticas/{localidad}  -> estadísticas de una localidad
  GET  /resumen                   -> resumen general ciudad
"""

import sys
from pathlib import Path

# Agregar el directorio padre al path para importar mapvete
sys.path.append(str(Path(__file__).parent.parent / "BACKEND"))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from typing import Optional
import mapvete

# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────
app = FastAPI(
    title="API Veterinarias Bogotá",
    description="Generador de ubicaciones de veterinarias en Bogotá con filtros geoespaciales",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Redirigir raíz al frontend ──────────────
@app.get("/app", include_in_schema=False)
def frontend_redirect():
    return RedirectResponse(url="/app/index.html")

# ─── Servir archivos estáticos del Frontend ──
_frontend_path = Path(__file__).parent.parent / "Frontend"
app.mount("/app", StaticFiles(directory=str(_frontend_path), html=True), name="frontend")


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "mensaje": "API Veterinarias Bogotá activa"}


@app.get("/localidades", tags=["Mapa"])
def get_localidades():
    """Lista todas las localidades de Bogotá con su código y área."""
    return {"localidades": mapvete.get_localidades()}


@app.get("/localidad-por-punto", tags=["Mapa"])
def localidad_por_punto(
    lat: float = Query(..., description="Latitud del punto", examples={"default": {"value": 4.6532}}),
    lon: float = Query(..., description="Longitud del punto", examples={"default": {"value": -74.0836}}),
):
    """Detecta en qué localidad de Bogotá cae un punto geográfico."""
    localidad = mapvete.get_localidad_por_punto(lat, lon)
    if localidad is None:
        return {"localidad": None, "mensaje": "El punto no está dentro de ninguna localidad de Bogotá"}
    return {"localidad": localidad, "lat": lat, "lon": lon}


@app.get("/veterinarias/recargar", tags=["Veterinarias"])
def recargar_veterinarias():
    """Recarga veterinarias desde OpenStreetMap fusionado con datos de zona usuario."""
    nuevas = mapvete._fetch_veterinarias_osm()
    if nuevas:
        zona = [{**v, "localidad": "KENNEDY", "fuente": "local"} for v in mapvete._FALLBACK_ZONA_USUARIO]
        offset = len(nuevas)
        for v in zona:
            offset += 1
            v["id"] = offset
        mapvete.VETERINARIAS = nuevas + zona
        fuente = "OSM + zona usuario"
    else:
        mapvete.VETERINARIAS = mapvete._VETERINARIAS_FALLBACK
        fuente = "fallback local"
    return {"total": len(mapvete.VETERINARIAS), "fuente": fuente}


@app.get("/veterinarias", tags=["Veterinarias"])
def get_todas():
    """Retorna todas las veterinarias registradas en Bogotá."""
    return {"total": len(mapvete.VETERINARIAS), "veterinarias": mapvete.get_todas_veterinarias()}


@app.get("/veterinarias/buscar", tags=["Veterinarias"])
def buscar_veterinarias(
    lat: float = Query(..., description="Latitud de la dirección de consulta", examples={"default": {"value": 4.6532}}),
    lon: float = Query(..., description="Longitud de la dirección de consulta", examples={"default": {"value": -74.0836}}),
    radio_km: float = Query(5.0, description="Radio de búsqueda en kilómetros", ge=0.5, le=50),
    animal: Optional[str] = Query(None, description="Filtrar por tipo de animal: perros, gatos, aves, conejos, reptiles"),
    seguridad: Optional[str] = Query(None, description="Filtrar por seguridad de la zona: alta, media, baja"),
):
    """
    Busca veterinarias dentro de un radio (km) desde una dirección dada.
    Retorna resultados ordenados por distancia, con:
    - Nombre y teléfono
    - Distancia al punto consultado
    - Precio promedio del servicio
    - Seguridad de la zona
    - Calificación
    - Animales atendidos
    """
    localidad_origen = mapvete.get_localidad_por_punto(lat, lon)
    resultados = mapvete.buscar_veterinarias(lat, lon, radio_km, animal, seguridad)

    return {
        "punto_consulta": {"lat": lat, "lon": lon, "localidad": localidad_origen},
        "radio_km": radio_km,
        "filtros": {"animal": animal, "seguridad": seguridad},
        "total_encontradas": len(resultados),
        "veterinarias": resultados,
    }


@app.get("/veterinarias/{vet_id}", tags=["Veterinarias"])
def get_veterinaria(vet_id: int):
    """Retorna el detalle completo de una veterinaria por su ID."""
    vet = next((v for v in mapvete.VETERINARIAS if v["id"] == vet_id), None)
    if not vet:
        raise HTTPException(status_code=404, detail=f"Veterinaria con id {vet_id} no encontrada")
    return vet


@app.get("/estadisticas/{localidad}", tags=["Estadísticas"])
def estadisticas_localidad(localidad: str):
    """
    Estadísticas de veterinarias en una localidad específica:
    - Cantidad de veterinarias
    - Precio promedio del servicio
    - Calificación promedio
    - Seguridad predominante de la zona
    - Tipos de animales atendidos
    - Lista de veterinarias con contacto
    """
    stats = mapvete.get_estadisticas_localidad(localidad.upper())
    if stats.get("cantidad", 0) == 0:
        raise HTTPException(status_code=404, detail=f"No se encontraron veterinarias para la localidad '{localidad}'")
    return stats


@app.get("/resumen", tags=["Estadísticas"])
def resumen_ciudad():
    """Resumen general de veterinarias en toda Bogotá."""
    return mapvete.get_resumen_ciudad()


@app.get("/geojson-localidades", tags=["Mapa"])
def geojson_localidades():
    """
    Retorna las localidades en formato GeoJSON estándar (compatible con Leaflet).
    Convierte el formato ESRI a GeoJSON con geometría Polygon.
    """
    import json
    from pathlib import Path

    geo_path = Path(__file__).parent.parent / "Base de Datos" / "localidades.geojson"
    with open(geo_path, encoding="utf-8") as f:
        raw = json.load(f)

    features = []
    for feat in raw["features"]:
        attr = feat["attributes"]
        rings = feat["geometry"]["rings"]
        if not rings:
            continue
        geometry = {
            "type": "Polygon",
            "coordinates": rings
        }
        features.append({
            "type": "Feature",
            "properties": {
                "LocNombre": attr["LocNombre"],
                "LocCodigo": attr["LocCodigo"],
                "LocArea":   attr["LocArea"],
            },
            "geometry": geometry
        })

    return {"type": "FeatureCollection", "features": features}