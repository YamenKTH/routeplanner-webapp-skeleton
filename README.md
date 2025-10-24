Absolutely 🔥 — here’s a complete professional README.md you can use directly for your GitHub repository.
It’s designed for clarity (for anyone trying to run or deploy your project), includes OSRM setup instructions, Docker usage, and GitHub cleanliness notes.

# 🗺️ RoutePlanner Web App

A fully interactive route-planning web application that generates optimized walking tours using **FastAPI**, **Vue.js**, and the **OSRM routing engine**.  
Built to explore nearby points of interest, calculate efficient paths, and visualize them interactively on a map.  

---

## 🚀 Features

- 🌍 **Interactive map** with draggable start and end points  
- 🧭 **OSRM-based routing** for accurate walking times and paths  
- 🏙️ **Automatic POI loading** within adjustable radius  
- 🔁 Supports roundtrip and one-way routes  
- ⚙️ Fully containerized with **Docker Compose**  
- 🎨 Responsive UI that mimics a mobile map app layout  

---

## 🧱 Project Structure



routeplanner-webapp-skeleton/
├── backend/
│ ├── api.py # FastAPI application
│ ├── requirements.txt # Backend dependencies
│ ├── Scorer.py # Scoring logic for POIs
│ ├── app_explore5.py # POI exploration logic
│ ├── app_tour3.py # Tour planning logic
│ ├── cleanDatabase.py # DB utilities
│ └── osrm-data/ # ⬅️ Place OSRM map data here (see below)
│
├── frontend/
│ ├── src/ # Vue app source code
│ ├── package.json
│ └── ...
│
├── docker-compose.yml # Defines frontend + backend + OSRM containers
├── Dockerfile.backend # FastAPI build
├── Dockerfile.frontend # Vue + Nginx build
├── nginx.conf # Nginx config for frontend
├── .gitignore # Excludes heavy and build files
├── .dockerignore # Prevents Docker from re-uploading large data
└── README.md # This file


---

## 🐳 Running the app locally

Make sure you have **Docker Desktop** installed.

### 1️⃣ Clone the repository
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd routeplanner-webapp-skeleton

2️⃣ Prepare the OSRM map data

The app uses the Open Source Routing Machine (OSRM) for route calculation.
You need to download and preprocess an .osm.pbf map file before running.

📍 Example: Sweden

Download the latest Sweden map from Geofabrik:

https://download.geofabrik.de/europe/sweden.html

Save it inside:

backend/osrm-data/sweden-latest.osm.pbf


Then preprocess it using the official OSRM Docker image:

# Step 1: Extract routing data
docker run -t -v ${PWD}/backend/osrm-data:/data osrm/osrm-backend \
  osrm-extract -p /opt/osrm/profiles/foot.lua /data/sweden-latest.osm.pbf

# Step 2: Partition the data
docker run -t -v ${PWD}/backend/osrm-data:/data osrm/osrm-backend \
  osrm-partition /data/sweden-latest.osrm

# Step 3: Customize data for routing
docker run -t -v ${PWD}/backend/osrm-data:/data osrm/osrm-backend \
  osrm-customize /data/sweden-latest.osrm


✅ After this, your folder backend/osrm-data/ should contain several .osrm files:

sweden-latest.osm.pbf
sweden-latest.osrm
sweden-latest.osrm.cnbg
sweden-latest.osrm.datasource_names
sweden-latest.osrm.fileIndex
...

3️⃣ Build and run the entire stack
docker compose build
docker compose up


This will start 3 containers:

Service	Description	Port
frontend	Vue.js app served by Nginx	http://localhost:8080

backend	FastAPI server	http://localhost:8000

osrm	Routing engine (foot profile)	http://localhost:5000
4️⃣ Open the app

Visit:
👉 http://localhost:8080

Drag the red marker to change start location

Add or move green marker to define destination

Adjust time and radius sliders on the sides

Click the magnifier button 🔍 to build the route

🧪 Health checks
Endpoint	Description	Example Output
/api/health	Backend status	{"ok": true, "uses_real_stack": true}
/api/pois	Returns nearby points of interest	GeoJSON FeatureCollection
/api/tour	Generates optimized route	Tour JSON with path + stops
⚙️ Environment Variables
Variable	Description	Default
OSRM_URL	Internal URL of the OSRM container	http://osrm:5000
CACHE_DB	Optional database file for POIs	out/stockholm_wiki.db
💾 .gitignore and .dockerignore setup

To keep the repository lightweight, large map data and temporary files are excluded.

.gitignore

__pycache__/
*.pyc
.env
node_modules/
frontend/node_modules/
dist/
backend/osrm-data/
*.osrm
*.osm.pbf
*.db
*.log


.dockerignore

backend/osrm-data
__pycache__/
node_modules
frontend/node_modules
dist
.git
.env

🌐 Deployment Options

This app is fully Dockerized, so you can deploy it anywhere Docker runs:

✅ Recommended free hosts:
Platform	Supports Docker Compose	Free Tier	Notes
Railway.app	✅ Yes	🆓 500 hrs/month	Easiest full deployment
Koyeb.com	✅ Yes	🆓 2 free containers	Lightweight
Render.com	⚠️ Partially	🆓 1 web service	Backend + static frontend only
Oracle Cloud Free VM	✅ Full Docker	🆓 Always free	Advanced setup
To deploy on Railway:

Push your repo to GitHub

Log into https://railway.app

“New Project → Deploy from GitHub”

Railway will detect your Docker Compose setup

Add environment variable:

OSRM_URL=http://osrm:5000


Create a persistent volume for /data

Upload your .osrm files there via Railway Shell

🧠 Troubleshooting
Issue	Fix
502 Bad Gateway	Backend container crashed — check logs via docker compose logs backend
400 Bad Request	CORS issue — ensure backend origins includes http://localhost:8080
OSRM not found	Check that your .osrm files exist in backend/osrm-data/
Slow build	Add backend/osrm-data to .dockerignore
👩‍💻 Contributors

Developed by:
Yamen Alkattab

Project guided by course work in Applied Machine Learning & Web Systems.

 License

MIT License.
Feel free to use, modify, and share this project with proper attribution.

🌟 If you found this helpful, consider starring the repo on GitHub!