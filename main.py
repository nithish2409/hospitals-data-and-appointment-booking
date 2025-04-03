from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

# Enable CORS (Allows frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Mount static directory correctly
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Load hospital data from CSV
csv_path = "hospitals_coimbatore.csv"
try:
    df = pd.read_csv(csv_path, dtype=str)  # Ensure all data is treated as string
    df.fillna("", inplace=True)  # Replace NaN values with empty strings
except Exception as e:
    print(f"Error loading CSV: {e}")
    df = pd.DataFrame(columns=["Name", "Location", "Distance"])  # Fallback empty DataFrame

@app.get("/")
def read_root():
    """Root endpoint to check if API is running."""
    return {"message": "API is running. Visit /static/index.html for UI."}

@app.get("/search")
def search_hospitals(location: str = Query("")):
    """Search hospitals where the 'Location' column contains the user input (case-insensitive, flexible match)."""

    if not location.strip():
        return df.to_dict(orient="records")  # If no search input, return all hospitals

    # Convert search query and hospital locations to lowercase
    location = location.lower().strip()

    # 🔥 Improve matching by splitting input into words and checking if all exist in Location
    def match_location(hospital_location):
        hospital_location = hospital_location.lower()  # Convert to lowercase
        words = location.split()  # Split search query into words
        return all(word in hospital_location for word in words)  # Ensure all words exist in location

    # Apply search filter
    filtered_df = df[df["Location"].apply(match_location)]

    print(f"🔍 Search Query: '{location}' → {len(filtered_df)} results found")  # Debugging

    return filtered_df.to_dict(orient="records")

@app.get("/get_hospital")
def get_hospital(name: str = Query(...), location: str = Query(...)):
    """Fetch a specific hospital based on exact name and location."""

    # Ensure case-insensitive comparison
    hospital = df[
        (df["Name"].str.lower() == name.lower().strip()) & 
        (df["Location"].str.lower() == location.lower().strip())
    ]

    if hospital.empty:
        return {"detail": "Hospital not found"}

    return hospital.to_dict(orient="records")[0]  # Return first match
