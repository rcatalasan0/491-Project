# 📈 Stock Market Predictor – Defense Sector

## Overview
A capstone project that develops a **Stock Market Predictor** for the **defense sector** (e.g., Lockheed Martin, Boeing, Raytheon, Northrop Grumman).  
The system combines **C++/SQL backend services**, **machine learning models**, and **real-time stock data** with an interactive **React.js frontend**.

---

## Features
- Real-time + historical stock data ingestion  
- Machine learning models for price prediction  
- Interactive dashboards and visualizations  
- Portfolio simulation and watchlists  
- Secure authentication (JWT/OAuth2)  
- Automated reports and alerts  

---

## Architecture
- **Frontend:** React.js  
- **Backend:** C++ APIs, Python ML (FastAPI/Flask)  
- **Database:** PostgreSQL + Redis cache  
- **Deployment:** Docker + GitHub Actions (CI/CD → AWS/Netlify)  
- **Patterns:** Microservices, MVC, Observer  

---

## Testing
- Unit: GoogleTest (C++), PyTest (Python)
- Integration: API + DB
- Load: Locust/JMeter
- Security: Static analysis + SQL injection checks


## CI/CD
CI: GitHub Actions run build + tests on PRs
CD: Dockerized deployments to staging/prod
Automation: Linting, security scans, test coverage

## Team
Christopher Contreras
Richard Nguyen
Alex Martinez
Rocco Catalasan
