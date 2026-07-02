# Mobile Recharge Application

A full stack mobile recharge application built with Python Flask and MySQL, containerized with Docker and deployed on Kubernetes.

###### Tech Stack
- Python 3.12
- Flask 3.1.3
- MySQL 8.0
- Docker
- Kubernetes
- Minikube

## Project Structure
recharge-app/
├── app/
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   └── templates/
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html
│       ├── recharge.html
│       └── transactions.html
├── mysql-secret.yaml
├── mysql-configmap.yaml
├── mysql-deployment.yaml
├── mysql-service.yaml
├── app-deployment.yaml
├── app-service.yaml
└── README.md

## Features
- User registration and login
- Mobile recharge for Jazz, Telenor, Zong, Ufone and SCO
- Transaction history
- Balance management
- Rs. 1000 welcome bonus on registration

## Kubernetes Resources
| Resource | Name | Purpose |
|----------|------|---------|
| Secret | mysql-secret | Stores MySQL credentials securely |
| ConfigMap | mysql-configmap | Stores non-sensitive configuration |
| PVC | mysql-pvc | Persists MySQL data |
| Deployment | mysql-deployment | Manages MySQL pod |
| Service | mysql-service | Exposes MySQL inside cluster (ClusterIP) |
| Deployment | recharge-deployment | Manages Flask app pods |
| Service | recharge-service | Exposes app via NodePort |

## Deploy to Kubernetes
```bash
kubectl apply -f mysql-secret.yaml
kubectl apply -f mysql-configmap.yaml
kubectl apply -f mysql-deployment.yaml
kubectl apply -f mysql-service.yaml
kubectl apply -f app-deployment.yaml
kubectl apply -f app-service.yaml
```

## Access the App
```bash
minikube service recharge-service --url
```

## DockerHub
https://hub.docker.com/r/rashidali007/recharge-app

## GitHub
https://github.com/rashid-007/recharge-repo
