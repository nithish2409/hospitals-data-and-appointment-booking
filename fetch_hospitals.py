import requests
import json
import pandas as pd
import concurrent.futures
from time import sleep
from opencage.geocoder import OpenCageGeocode

# Overpass API endpoint
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# OpenCage API Key
OPENCAGE_API_KEY = "7d5ff2fb04ef45d1a799ba084fbc08a3"
geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

# Overpass QL query to get hospitals in Coimbatore
query = """
[out:json];
area[name="Coimbatore"]->.searchArea;
(
  node["amenity"="hospital"](area.searchArea);
  way["amenity"="hospital"](area.searchArea);
  relation["amenity"="hospital"](area.searchArea);
);
out center;
"""

# Fetch hospital data from Overpass API
response = requests.get(OVERPASS_URL, params={"data": query})
data = response.json()

# Function to get address using OpenCage API (with retries)
def get_address(lat, lon, retries=3):
    if lat is None or lon is None:
        return "Address not found"

    for attempt in range(retries):
        try:
            result = geocoder.reverse_geocode(lat, lon)
            if result:
                return result[0]['formatted']
        except Exception as e:
            print(f"⚠️ OpenCage API Error: {e} (attempt {attempt+1}/{retries})")
            sleep(1)  # Short delay before retrying

    return "Address not found"

# Extract hospital details
hospitals = []
for element in data["elements"]:
    name = element.get("tags", {}).get("name", "Unknown Hospital")
    lat = element.get("lat", element.get("center", {}).get("lat"))
    lon = element.get("lon", element.get("center", {}).get("lon"))
    
    hospitals.append({"Name": name, "Latitude": lat, "Longitude": lon})

# Function to process hospitals in parallel
def process_hospital(hospital):
    hospital["Location"] = get_address(hospital["Latitude"], hospital["Longitude"])
    return hospital

# Use ThreadPoolExecutor for parallel processing (10 threads)
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    hospitals = list(executor.map(process_hospital, hospitals))

# Convert to DataFrame
df = pd.DataFrame(hospitals)

# Save to CSV file
df.to_csv("hospitals_coimbatore.csv", index=False)

# Print results
print(df)
print("\n✅ Data saved to 'hospitals_coimbatore.csv'")
