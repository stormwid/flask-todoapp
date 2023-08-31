# Setup Google Cloud
- Google Cloud Projekt erstellen
- App Engine aktivieren
- Unter Cloud SQL mySql Instanz erstellen
- Unter mySql eine DB erstellen
- Im IAM dem App Engine default service account die Rollen Cloud SQL Client und Cloud SQL Editor zuweisen
- Unter API and Services Cloud Logging API, Compute Engine API,  Cloud Pub/Sub API, Cloud SQL Admin API aktivieren falls nicht bereits aktiviert

# App Deployment
- Google Cloud CLI https://cloud.google.com/sdk/docs/install?hl=de#windows installieren und konfigurieren
- In das Directory wo flask-todoapp gespeichert wurde wechseln
- "gcloud app deploy" Befehl absetzen
