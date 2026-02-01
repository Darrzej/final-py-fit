FitAI Ultimate is a professional-grade fitness tracking application that combines a FastAPI backend with a Streamlit frontend to provide automated, data-driven coaching. The system leverages AI-driven logic to analyze strength trends, metabolic consistency, and nutritional adherence based on user-specific biometrics and goals.

🚀 Key Features
Intelligent AI Coach: Analyzes performance "Deltas" (progress between sessions) and provides tactical feedback on strength standards and recovery.

Interactive Analytics: Visualizes caloric intake versus protein consumption and tracks strength progression over time using high-fidelity Plotly charts.

Dynamic Training Program: Allows users to build custom routines from a master exercise library and log PRs in real-time.

Admin Command Center: A global management interface for administrators to monitor users, manage exercise databases, and audit logs.

Biometric Calculators: Includes 1RM (One Rep Max) predictors and training zone calculators.

🛠️ Technical Stack
The project is built using a strictly Python-based architecture, utilizing the following libraries:

Frontend: streamlit, pandas, numpy, plotly, requests.

Backend: fastapi, pydantic, uvicorn.

Data Models: Strict schema validation using Pydantic models for Users, Exercises, and Nutrition logs.

uvicorn main:app --reload

streamlit run main.py

ADMIN ACCOUNT:
USERNAME: Darsej
PASSWORD: 1234
