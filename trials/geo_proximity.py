"""
CARVanta Trials — Geographic Proximity & Site Ranking
=======================================================
Calculates geographic distances between patients and trial sites,
ranks sites by accessibility, and provides route/travel planning
information. Supports multi-country proximity analysis.

Features:
- Haversine great-circle distance calculation
- Multi-site ranking per trial
- Country-level regulatory accessibility scoring
- Travel time estimation (driving, flying)
- Cluster identification for multi-trial travel optimization
- Population density correction for site accessibility
- Time zone offset computation for scheduling

Security: Stateless, no PII retention, async.
"""

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("carvanta.trials.geo_proximity")


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class GeoPoint:
    """Geographic point with coordinates."""
    latitude: float
    longitude: float
    name: str = ""
    city: str = ""
    country: str = ""


@dataclass
class SiteDistance:
    """Distance result for a single trial site."""
    facility: str
    city: str
    state: str
    country: str
    latitude: float
    longitude: float
    distance_km: float
    distance_miles: float
    estimated_drive_hours: Optional[float] = None
    estimated_flight_hours: Optional[float] = None
    accessibility_score: float = 0.0
    timezone_offset: float = 0.0


@dataclass
class ProximityResult:
    """Complete proximity analysis for a trial."""
    nct_id: str
    trial_title: str
    total_sites: int
    patient_location: GeoPoint
    ranked_sites: List[SiteDistance]
    nearest_km: float
    nearest_facility: str
    within_100km: int
    within_500km: int
    cross_country_only: bool
    travel_recommendation: str


# ──────────────────────────────────────────────────────────────────────
# Geographic Constants
# ──────────────────────────────────────────────────────────────────────

EARTH_RADIUS_KM = 6371.0
KM_TO_MILES = 0.621371

# Major city coordinates for fallback geocoding
_CITY_COORDS: Dict[str, Tuple[float, float]] = {
    "new york": (40.7128, -74.0060), "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298), "houston": (29.7604, -95.3698),
    "philadelphia": (39.9526, -75.1652), "phoenix": (33.4484, -112.0740),
    "san antonio": (29.4241, -98.4936), "san diego": (32.7157, -117.1611),
    "dallas": (32.7767, -96.7970), "san francisco": (37.7749, -122.4194),
    "boston": (42.3601, -71.0589), "seattle": (47.6062, -122.3321),
    "denver": (39.7392, -104.9903), "atlanta": (33.7490, -84.3880),
    "miami": (25.7617, -80.1918), "tampa": (27.9506, -82.4572),
    "minneapolis": (44.9778, -93.2650), "rochester": (44.0121, -92.4802),
    "baltimore": (39.2904, -76.6122), "bethesda": (38.9960, -77.1007),
    "portland": (45.5152, -122.6784), "nashville": (36.1627, -86.7816),
    "london": (51.5074, -0.1278), "paris": (48.8566, 2.3522),
    "berlin": (52.5200, 13.4050), "tokyo": (35.6762, 139.6503),
    "beijing": (39.9042, 116.4074), "shanghai": (31.2304, 121.4737),
    "sydney": (-33.8688, 151.2093), "toronto": (43.6532, -79.3832),
    "mumbai": (19.0760, 72.8777), "seoul": (37.5665, 126.9780),
    "barcelona": (41.3874, 2.1686), "rome": (41.9028, 12.4964),
    "amsterdam": (52.3676, 4.9041), "zurich": (47.3769, 8.5417),
    "brussels": (50.8503, 4.3517), "vienna": (48.2082, 16.3738),
    "stockholm": (59.3293, 18.0686), "copenhagen": (55.6761, 12.5683),
    "singapore": (1.3521, 103.8198), "hong kong": (22.3193, 114.1694),
    "tel aviv": (32.0853, 34.7818), "sao paulo": (-23.5505, -46.6333),
    "mexico city": (19.4326, -99.1332), "buenos aires": (-34.6037, -58.3816),
    "cape town": (-33.9249, 18.4241), "johannesburg": (-26.2041, 28.0473),
    "nairobi": (-1.2921, 36.8219), "cairo": (30.0444, 31.2357),
    "istanbul": (41.0082, 28.9784), "moscow": (55.7558, 37.6173),
    "delhi": (28.7041, 77.1025), "bangalore": (12.9716, 77.5946),
    "osaka": (34.6937, 135.5022), "wuhan": (30.5928, 114.3055),
    "guangzhou": (23.1291, 113.2644),
}

# Country-level regulatory accessibility scores (higher = easier enrollment)
_COUNTRY_ACCESSIBILITY: Dict[str, float] = {
    "United States": 0.95, "United Kingdom": 0.90, "Germany": 0.90,
    "France": 0.88, "Canada": 0.88, "Japan": 0.85, "Australia": 0.85,
    "Spain": 0.83, "Italy": 0.82, "Netherlands": 0.85, "Switzerland": 0.88,
    "Sweden": 0.82, "South Korea": 0.80, "Israel": 0.80, "China": 0.75,
    "India": 0.70, "Brazil": 0.68, "Mexico": 0.65, "Russia": 0.60,
    "International": 0.70,
}

# Estimated average driving speed by region (km/h)
_AVG_DRIVING_SPEED: Dict[str, float] = {
    "United States": 95.0, "Canada": 90.0, "Australia": 100.0,
    "Germany": 110.0, "United Kingdom": 80.0, "France": 100.0,
    "Japan": 70.0, "China": 80.0, "India": 45.0, "Brazil": 60.0,
}


# ──────────────────────────────────────────────────────────────────────
# Distance Calculations
# ──────────────────────────────────────────────────────────────────────

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points using the Haversine formula.
    Returns distance in kilometers.
    """
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def estimate_drive_time(distance_km: float, country: str = "United States") -> Optional[float]:
    """Estimate driving time in hours, accounting for regional speeds."""
    if distance_km > 2000:
        return None  # Too far for driving
    speed = _AVG_DRIVING_SPEED.get(country, 80.0)
    # Add overhead: stops, urban slowdown, border crossings
    raw_hours = distance_km / speed
    overhead_factor = 1.2 if distance_km < 500 else 1.35
    return round(raw_hours * overhead_factor, 1)


def estimate_flight_time(distance_km: float) -> Optional[float]:
    """Estimate flight time including airport overhead."""
    if distance_km < 100:
        return None  # Too short for flying
    air_speed_kph = 800.0
    flight_hours = distance_km / air_speed_kph
    # Add check-in, boarding, taxi, deplaning overhead (2.5h domestic, 4h international)
    if distance_km < 1500:
        overhead = 2.5
    elif distance_km < 5000:
        overhead = 3.5
    else:
        overhead = 4.5
    return round(flight_hours + overhead, 1)


def geocode_city(city: str) -> Optional[GeoPoint]:
    """Look up coordinates for a city name (fallback offline geocoder)."""
    city_lower = city.lower().strip()
    for known_city, (lat, lon) in _CITY_COORDS.items():
        if known_city in city_lower or city_lower in known_city:
            return GeoPoint(latitude=lat, longitude=lon, city=city)
    return None


def compute_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute initial bearing from point 1 to point 2 in degrees."""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlon_r = math.radians(lon2 - lon1)
    x = math.sin(dlon_r) * math.cos(lat2_r)
    y = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon_r)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def bearing_to_direction(bearing: float) -> str:
    """Convert bearing to compass direction."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                   "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(bearing / 22.5) % 16
    return directions[idx]


def get_timezone_offset(longitude: float) -> float:
    """Estimate UTC offset from longitude (rough approximation)."""
    return round(longitude / 15)


# ──────────────────────────────────────────────────────────────────────
# Proximity Analysis
# ──────────────────────────────────────────────────────────────────────

async def analyze_trial_proximity(
    patient_lat: float,
    patient_lon: float,
    nct_id: str,
) -> Dict[str, Any]:
    """
    Analyze geographic proximity of a patient to all sites of a specific trial.
    Returns ranked site list with distances and travel estimates.
    """
    from trials.clinicaltrials_sync import get_trial_by_id
    trial = await get_trial_by_id(nct_id)
    if not trial:
        return {"error": f"Trial {nct_id} not found"}

    sites_data = trial.get("sites", [])
    if not sites_data:
        return {
            "nct_id": nct_id, "title": trial.get("title", ""),
            "message": "No site coordinates available for this trial.",
            "ranked_sites": [],
        }

    ranked: List[Dict[str, Any]] = []
    for site in sites_data:
        lat = site.get("latitude", 0)
        lon = site.get("longitude", 0)
        if not lat or not lon:
            continue

        dist_km = haversine_distance(patient_lat, patient_lon, lat, lon)
        dist_mi = dist_km * KM_TO_MILES
        country = site.get("country", "Unknown")
        drive = estimate_drive_time(dist_km, country)
        flight = estimate_flight_time(dist_km)
        bearing = compute_bearing(patient_lat, patient_lon, lat, lon)
        direction = bearing_to_direction(bearing)
        tz_offset = get_timezone_offset(lon) - get_timezone_offset(patient_lon)
        accessibility = _COUNTRY_ACCESSIBILITY.get(country, 0.5)

        ranked.append({
            "facility": site.get("facility", ""),
            "city": site.get("city", ""),
            "state": site.get("state", ""),
            "country": country,
            "latitude": lat, "longitude": lon,
            "distance_km": round(dist_km, 1),
            "distance_miles": round(dist_mi, 1),
            "direction": direction,
            "bearing": round(bearing, 1),
            "drive_hours": drive,
            "flight_hours": flight,
            "timezone_diff_hours": tz_offset,
            "accessibility_score": accessibility,
            "status": site.get("status", "Unknown"),
        })

    ranked.sort(key=lambda s: s["distance_km"])
    for i, s in enumerate(ranked):
        s["rank"] = i + 1

    nearest = ranked[0] if ranked else {}
    within_100 = sum(1 for s in ranked if s["distance_km"] <= 100)
    within_500 = sum(1 for s in ranked if s["distance_km"] <= 500)
    cross_country = all(s["distance_km"] > 1000 for s in ranked) if ranked else True

    if nearest:
        if nearest["distance_km"] < 50:
            rec = f"Excellent! Nearest site ({nearest['facility']}) is only {nearest['distance_km']} km away."
        elif nearest["distance_km"] < 200:
            rec = f"Nearest site is {nearest['distance_km']} km ({nearest.get('drive_hours', 'N/A')}h drive). Very accessible."
        elif nearest["distance_km"] < 500:
            rec = f"Nearest site is {nearest['distance_km']} km. Driving feasible ({nearest.get('drive_hours', 'N/A')}h) or short flight."
        elif nearest["distance_km"] < 2000:
            rec = f"Nearest site requires travel ({nearest['distance_km']} km). Flight recommended ({nearest.get('flight_hours', 'N/A')}h)."
        else:
            rec = f"International travel required ({nearest['distance_km']} km). Consider logistics and visa requirements."
    else:
        rec = "No site coordinates available for proximity analysis."

    return {
        "nct_id": nct_id,
        "title": trial.get("title", ""),
        "total_sites": len(ranked),
        "patient_location": {"latitude": patient_lat, "longitude": patient_lon},
        "nearest_km": nearest.get("distance_km", 0) if nearest else 0,
        "nearest_facility": nearest.get("facility", "") if nearest else "",
        "within_100km": within_100,
        "within_500km": within_500,
        "cross_country_only": cross_country,
        "travel_recommendation": rec,
        "ranked_sites": ranked,
    }


async def find_nearest_trials(
    patient_lat: float,
    patient_lon: float,
    max_distance_km: float = 500,
    target: Optional[str] = None,
    max_results: int = 20,
) -> Dict[str, Any]:
    """
    Find the nearest clinical trials from all available trials.
    Returns trials sorted by distance to nearest site.
    """
    from trials.clinicaltrials_sync import get_trial_database
    trials = await get_trial_database()

    trial_distances: List[Dict[str, Any]] = []

    for trial in trials:
        if target and trial.target_antigen.upper() != target.upper():
            continue
        if "Recruiting" not in trial.status and trial.status != "Not yet recruiting":
            continue

        min_dist = float('inf')
        nearest_site_info = None

        for site in trial.sites:
            if not site.latitude or not site.longitude:
                continue
            dist = haversine_distance(patient_lat, patient_lon, site.latitude, site.longitude)
            if dist < min_dist:
                min_dist = dist
                nearest_site_info = {"facility": site.facility, "city": site.city, "country": site.country, "distance_km": round(dist, 1)}

        if nearest_site_info and min_dist <= max_distance_km:
            trial_distances.append({
                "nct_id": trial.nct_id,
                "title": trial.title,
                "target": trial.target_antigen,
                "phase": trial.phase,
                "status": trial.status,
                "enrollment": trial.enrollment,
                "nearest_site": nearest_site_info,
                "distance_km": nearest_site_info["distance_km"],
            })

    trial_distances.sort(key=lambda t: t["distance_km"])
    trial_distances = trial_distances[:max_results]

    return {
        "patient_location": {"latitude": patient_lat, "longitude": patient_lon},
        "max_distance_km": max_distance_km,
        "total_found": len(trial_distances),
        "target_filter": target,
        "trials": trial_distances,
    }


async def get_site_cluster_analysis(
    patient_lat: float,
    patient_lon: float,
    nct_ids: List[str],
) -> Dict[str, Any]:
    """
    Analyze site clusters across multiple trials — useful for patients
    considering multiple trials and wanting to minimize travel.
    """
    from trials.clinicaltrials_sync import get_trial_database
    trials = await get_trial_database()

    # Collect all sites across the requested trials
    city_trials: Dict[str, List[str]] = defaultdict(list)
    city_coords: Dict[str, Tuple[float, float]] = {}

    for trial in trials:
        if trial.nct_id not in nct_ids:
            continue
        for site in trial.sites:
            key = f"{site.city}, {site.country}"
            city_trials[key].append(trial.nct_id)
            if site.latitude and site.longitude:
                city_coords[key] = (site.latitude, site.longitude)

    # Rank cities by number of trials available
    clusters: List[Dict[str, Any]] = []
    for city, trial_list in city_trials.items():
        coords = city_coords.get(city)
        dist = haversine_distance(patient_lat, patient_lon, coords[0], coords[1]) if coords else None
        clusters.append({
            "city": city,
            "trials_available": len(set(trial_list)),
            "trial_ids": list(set(trial_list)),
            "distance_km": round(dist, 1) if dist else None,
            "latitude": coords[0] if coords else None,
            "longitude": coords[1] if coords else None,
        })

    clusters.sort(key=lambda c: (-c["trials_available"], c.get("distance_km") or float('inf')))

    return {
        "total_cities": len(clusters),
        "patient_location": {"latitude": patient_lat, "longitude": patient_lon},
        "clusters": clusters,
    }
