"""
SkyGuard AI — 32+ Pan-India IMD Automatic Weather Station Registry
Spans all major meteorological subdivisions across India.
"""

from typing import Dict, Any, List
import math

STATIONS: Dict[str, Dict[str, Any]] = {
    # ── NORTH ZONE ──
    "Delhi (Safdarjung)": {
        "id": "DEL01", "name": "Delhi Safdarjung", "state": "Delhi",
        "zone": "North", "lat": 28.5849, "lon": 77.2083, "elevation_m": 216,
        "imd_code": "42182", "wmo_id": "421820", "type": "Principal AWS"
    },
    "Delhi (Palam)": {
        "id": "DEL02", "name": "Delhi Palam", "state": "Delhi",
        "zone": "North", "lat": 28.5665, "lon": 77.1031, "elevation_m": 237,
        "imd_code": "42181", "wmo_id": "421810", "type": "Airport AWS"
    },
    "Srinagar": {
        "id": "SXR01", "name": "Srinagar (Badgam)", "state": "Jammu & Kashmir",
        "zone": "North (Himalayan)", "lat": 34.0837, "lon": 74.7973, "elevation_m": 1587,
        "imd_code": "42027", "wmo_id": "420270", "type": "High Altitude AWS"
    },
    "Leh Ladakh": {
        "id": "IXL01", "name": "Leh (Ladakh)", "state": "Ladakh",
        "zone": "North (High Altitude)", "lat": 34.1526, "lon": 77.5771, "elevation_m": 3514,
        "imd_code": "42005", "wmo_id": "420050", "type": "Extreme Alpine AWS"
    },
    "Shimla": {
        "id": "SLV01", "name": "Shimla (Ridge)", "state": "Himachal Pradesh",
        "zone": "North (Himalayan)", "lat": 31.1048, "lon": 77.1734, "elevation_m": 2205,
        "imd_code": "42083", "wmo_id": "420830", "type": "Mountain AWS"
    },
    "Dehradun": {
        "id": "DED01", "name": "Dehradun", "state": "Uttarakhand",
        "zone": "North", "lat": 30.3165, "lon": 78.0322, "elevation_m": 682,
        "imd_code": "42111", "wmo_id": "421110", "type": "Sub-Himalayan AWS"
    },
    "Chandigarh": {
        "id": "IXC01", "name": "Chandigarh", "state": "Punjab / Haryana",
        "zone": "North", "lat": 30.7333, "lon": 76.7794, "elevation_m": 321,
        "imd_code": "42131", "wmo_id": "421310", "type": "Principal AWS"
    },
    "Amritsar": {
        "id": "ATQ01", "name": "Amritsar", "state": "Punjab",
        "zone": "North", "lat": 31.6340, "lon": 74.8723, "elevation_m": 234,
        "imd_code": "42071", "wmo_id": "420710", "type": "Plain AWS"
    },
    "Jaipur (Sanganer)": {
        "id": "JAI01", "name": "Jaipur Sanganer", "state": "Rajasthan",
        "zone": "North-West", "lat": 26.8240, "lon": 75.8120, "elevation_m": 390,
        "imd_code": "42348", "wmo_id": "423480", "type": "Semi-Arid AWS"
    },
    "Lucknow (Amausi)": {
        "id": "LKO01", "name": "Lucknow Amausi", "state": "Uttar Pradesh",
        "zone": "North-Central", "lat": 26.7606, "lon": 80.8893, "elevation_m": 128,
        "imd_code": "42369", "wmo_id": "423690", "type": "Gangetic Plain AWS"
    },
    "Varanasi (Babatpur)": {
        "id": "VNS01", "name": "Varanasi Babatpur", "state": "Uttar Pradesh",
        "zone": "North-Central", "lat": 25.4497, "lon": 82.8587, "elevation_m": 85,
        "imd_code": "42475", "wmo_id": "424750", "type": "Gangetic Plain AWS"
    },

    # ── WEST & CENTRAL ZONE ──
    "Mumbai (Colaba)": {
        "id": "BOM01", "name": "Mumbai Colaba", "state": "Maharashtra",
        "zone": "West (Coastal)", "lat": 18.9067, "lon": 72.8147, "elevation_m": 14,
        "imd_code": "43003", "wmo_id": "430030", "type": "Coastal AWS"
    },
    "Mumbai (Santa Cruz)": {
        "id": "BOM02", "name": "Mumbai Santa Cruz", "state": "Maharashtra",
        "zone": "West (Coastal)", "lat": 19.1176, "lon": 72.8631, "elevation_m": 19,
        "imd_code": "43057", "wmo_id": "430570", "type": "Airport AWS"
    },
    "Pune (Shivajinagar)": {
        "id": "PNQ01", "name": "Pune Shivajinagar", "state": "Maharashtra",
        "zone": "West (Deccan)", "lat": 18.5314, "lon": 73.8446, "elevation_m": 560,
        "imd_code": "43063", "wmo_id": "430630", "type": "Plateau AWS"
    },
    "Ahmedabad": {
        "id": "AMD01", "name": "Ahmedabad", "state": "Gujarat",
        "zone": "West", "lat": 23.0666, "lon": 72.6323, "elevation_m": 55,
        "imd_code": "42647", "wmo_id": "426470", "type": "Urban AWS"
    },
    "Surat": {
        "id": "STV01", "name": "Surat", "state": "Gujarat",
        "zone": "West (Coastal)", "lat": 21.1702, "lon": 72.8311, "elevation_m": 13,
        "imd_code": "42840", "wmo_id": "428400", "type": "Coastal AWS"
    },
    "Jodhpur": {
        "id": "JDH01", "name": "Jodhpur", "state": "Rajasthan",
        "zone": "West (Thar)", "lat": 26.2389, "lon": 73.0243, "elevation_m": 224,
        "imd_code": "42339", "wmo_id": "423390", "type": "Arid Desert AWS"
    },
    "Bhopal (Bairagarh)": {
        "id": "BHO01", "name": "Bhopal Bairagarh", "state": "Madhya Pradesh",
        "zone": "Central", "lat": 23.2868, "lon": 77.3483, "elevation_m": 523,
        "imd_code": "42667", "wmo_id": "426670", "type": "Central Plateau AWS"
    },
    "Nagpur (Sonegaon)": {
        "id": "NAG01", "name": "Nagpur Sonegaon", "state": "Maharashtra",
        "zone": "Central", "lat": 21.0922, "lon": 79.0607, "elevation_m": 310,
        "imd_code": "42867", "wmo_id": "428670", "type": "Vidarbha AWS"
    },
    "Panaji (Goa)": {
        "id": "GOI01", "name": "Panaji (Goa)", "state": "Goa",
        "zone": "West (Konkan)", "lat": 15.4909, "lon": 73.8278, "elevation_m": 15,
        "imd_code": "43192", "wmo_id": "431920", "type": "Coastal AWS"
    },

    # ── EAST & NORTH-EAST ZONE ──
    "Kolkata (Alipore)": {
        "id": "CCU01", "name": "Kolkata Alipore", "state": "West Bengal",
        "zone": "East", "lat": 22.5354, "lon": 88.3358, "elevation_m": 9,
        "imd_code": "42807", "wmo_id": "428070", "type": "Principal Coastal AWS"
    },
    "Patna": {
        "id": "PAT01", "name": "Patna", "state": "Bihar",
        "zone": "East", "lat": 25.5941, "lon": 85.1376, "elevation_m": 53,
        "imd_code": "42492", "wmo_id": "424920", "type": "Gangetic Plain AWS"
    },
    "Bhubaneswar": {
        "id": "BBI01", "name": "Bhubaneswar", "state": "Odisha",
        "zone": "East (Coastal)", "lat": 20.2961, "lon": 85.8245, "elevation_m": 45,
        "imd_code": "42971", "wmo_id": "429710", "type": "Cyclone Prone AWS"
    },
    "Ranchi": {
        "id": "IXR01", "name": "Ranchi", "state": "Jharkhand",
        "zone": "East", "lat": 23.3441, "lon": 85.3096, "elevation_m": 651,
        "imd_code": "42701", "wmo_id": "427010", "type": "Plateau AWS"
    },
    "Raipur": {
        "id": "RPR01", "name": "Raipur", "state": "Chhattisgarh",
        "zone": "East-Central", "lat": 21.2514, "lon": 81.6296, "elevation_m": 298,
        "imd_code": "42874", "wmo_id": "428740", "type": "Plain AWS"
    },
    "Guwahati": {
        "id": "GAU01", "name": "Guwahati (Borjhar)", "state": "Assam",
        "zone": "North-East", "lat": 26.1061, "lon": 91.5859, "elevation_m": 54,
        "imd_code": "42410", "wmo_id": "424100", "type": "Brahmaputra Valley AWS"
    },
    "Shillong": {
        "id": "SHL01", "name": "Shillong", "state": "Meghalaya",
        "zone": "North-East (Hill)", "lat": 25.5788, "lon": 91.8933, "elevation_m": 1525,
        "imd_code": "42516", "wmo_id": "425160", "type": "High Rainfall AWS"
    },
    "Agartala": {
        "id": "IXA01", "name": "Agartala", "state": "Tripura",
        "zone": "North-East", "lat": 23.8315, "lon": 91.2868, "elevation_m": 16,
        "imd_code": "42724", "wmo_id": "427240", "type": "Valley AWS"
    },

    # ── SOUTH & ISLAND ZONE ──
    "Bengaluru (HAL)": {
        "id": "BLR01", "name": "Bengaluru HAL", "state": "Karnataka",
        "zone": "South (Deccan)", "lat": 12.9499, "lon": 77.6681, "elevation_m": 920,
        "imd_code": "43295", "wmo_id": "432950", "type": "Plateau AWS"
    },
    "Chennai (Nungambakkam)": {
        "id": "MAA01", "name": "Chennai Nungambakkam", "state": "Tamil Nadu",
        "zone": "South (Coromandel)", "lat": 13.0660, "lon": 80.2399, "elevation_m": 16,
        "imd_code": "43279", "wmo_id": "432790", "type": "Principal Coastal AWS"
    },
    "Hyderabad (Begumpet)": {
        "id": "HYD01", "name": "Hyderabad Begumpet", "state": "Telangana",
        "zone": "South (Deccan)", "lat": 17.4531, "lon": 78.4677, "elevation_m": 536,
        "imd_code": "43128", "wmo_id": "431280", "type": "Deccan AWS"
    },
    "Visakhapatnam": {
        "id": "VTZ01", "name": "Visakhapatnam", "state": "Andhra Pradesh",
        "zone": "South (Coastal)", "lat": 17.6868, "lon": 83.2185, "elevation_m": 22,
        "imd_code": "43149", "wmo_id": "431490", "type": "Coastal Port AWS"
    },
    "Kochi": {
        "id": "COK01", "name": "Kochi (Nedumbassery)", "state": "Kerala",
        "zone": "South (Malabar)", "lat": 10.1518, "lon": 76.3930, "elevation_m": 10,
        "imd_code": "43355", "wmo_id": "433550", "type": "Tropical Coastal AWS"
    },
    "Thiruvananthapuram": {
        "id": "TRV01", "name": "Thiruvananthapuram", "state": "Kerala",
        "zone": "South (Malabar)", "lat": 8.4826, "lon": 76.9521, "elevation_m": 64,
        "imd_code": "43371", "wmo_id": "433710", "type": "Monsoon Entry AWS"
    },
    "Port Blair (Andaman)": {
        "id": "IXZ01", "name": "Port Blair (Andaman)", "state": "Andaman & Nicobar",
        "zone": "Island Territory", "lat": 11.6234, "lon": 92.7265, "elevation_m": 16,
        "imd_code": "43333", "wmo_id": "433330", "type": "Island Maritime AWS"
    }
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great circle distance in kilometers."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def get_nearby_stations(station_name: str, max_distance_km: float = 800.0) -> List[str]:
    """Return list of nearby station keys sorted by distance."""
    if station_name not in STATIONS:
        return []
    target = STATIONS[station_name]
    nearby = []
    for name, s in STATIONS.items():
        if name == station_name:
            continue
        dist = haversine_distance(target["lat"], target["lon"], s["lat"], s["lon"])
        if dist <= max_distance_km:
            nearby.append((name, dist))
    nearby.sort(key=lambda x: x[1])
    return [n[0] for n in nearby]
