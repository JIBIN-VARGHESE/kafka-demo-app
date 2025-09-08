# Deployment Guide

## Overview

This guide provides instructions for deploying the Kafka Demo App in different environments.

## Local Development

### Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your Confluent Cloud credentials (see CONFIGURATION.md)
4. Run the demo UI: `streamlit run demo_ui.py`

### Manual Service Deployment

```bash
# Start each service in separate terminals
python order_producer.py
python fulfillment_service.py
python picklist_consumer.py
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command (can be overridden)
CMD ["python", "order_producer.py"]
```

### Docker Compose

```yaml
version: "3.8"
services:
  order-producer:
    build: .
    command: python order_producer.py
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
      - SCHEMA_REGISTRY_URL=${SCHEMA_REGISTRY_URL}
      - OAUTH_TOKEN_URL=${OAUTH_TOKEN_URL}
      - CLIENT_SECRET=${PRODUCER_CLIENT_SECRET}
    restart: unless-stopped

  fulfillment-service:
    build: .
    command: python fulfillment_service.py
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
      - SCHEMA_REGISTRY_URL=${SCHEMA_REGISTRY_URL}
      - OAUTH_TOKEN_URL=${OAUTH_TOKEN_URL}
      - CONSUMER_CLIENT_SECRET=${CONSUMER_CLIENT_SECRET}
      - PRODUCER_CLIENT_SECRET=${PRODUCER_CLIENT_SECRET}
    restart: unless-stopped

  picklist-consumer:
    build: .
    command: python picklist_consumer.py
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
      - SCHEMA_REGISTRY_URL=${SCHEMA_REGISTRY_URL}
      - OAUTH_TOKEN_URL=${OAUTH_TOKEN_URL}
      - CLIENT_SECRET=${CONSUMER_CLIENT_SECRET}
    restart: unless-stopped

  demo-ui:
    build: .
    command: streamlit run demo_ui.py --server.port 8501 --server.address 0.0.0.0
    ports:
      - "8501:8501"
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
```

## Kubernetes Deployment

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: kafka-demo
```

### ConfigMap for Kafka Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kafka-config
  namespace: kafka-demo
data:
  bootstrap-servers: "pkc-xxxxx.region.provider.confluent.cloud:9092"
  schema-registry-url: "https://psrc-xxxxx.region.provider.confluent.cloud"
  oauth-token-url: "https://xxxxx.confluent.cloud/oauth/token"
```

### Secret for OAuth Credentials

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kafka-secrets
  namespace: kafka-demo
type: Opaque
data:
  producer-client-secret: <base64-encoded-secret>
  consumer-client-secret: <base64-encoded-secret>
```

### Deployment for Order Producer

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-producer
  namespace: kafka-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: order-producer
  template:
    metadata:
      labels:
        app: order-producer
    spec:
      containers:
        - name: order-producer
          image: kafka-demo:latest
          command: ["python", "order_producer.py"]
          env:
            - name: KAFKA_BOOTSTRAP_SERVERS
              valueFrom:
                configMapKeyRef:
                  name: kafka-config
                  key: bootstrap-servers
            - name: SCHEMA_REGISTRY_URL
              valueFrom:
                configMapKeyRef:
                  name: kafka-config
                  key: schema-registry-url
            - name: OAUTH_TOKEN_URL
              valueFrom:
                configMapKeyRef:
                  name: kafka-config
                  key: oauth-token-url
            - name: CLIENT_SECRET
              valueFrom:
                secretKeyRef:
                  name: kafka-secrets
                  key: producer-client-secret
```

## Cloud Deployments

### AWS EKS

1. Create EKS cluster
2. Configure kubectl for cluster access
3. Apply Kubernetes manifests
4. Configure ALB for demo UI access

### Google GKE

1. Create GKE cluster
2. Configure kubectl for cluster access
3. Apply Kubernetes manifests
4. Configure load balancer for demo UI

### Azure AKS

1. Create AKS cluster
2. Configure kubectl for cluster access
3. Apply Kubernetes manifests
4. Configure Azure Load Balancer

## CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy Kafka Demo

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t kafka-demo:${{ github.sha }} .
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push kafka-demo:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/order-producer order-producer=kafka-demo:${{ github.sha }}
          kubectl set image deployment/fulfillment-service fulfillment-service=kafka-demo:${{ github.sha }}
          kubectl set image deployment/picklist-consumer picklist-consumer=kafka-demo:${{ github.sha }}
```

## Monitoring & Observability

### Prometheus Metrics

Add metrics collection to your services:

```python
from prometheus_client import Counter, Histogram, start_http_server

# Metrics
orders_produced = Counter('orders_produced_total', 'Total orders produced')
order_processing_time = Histogram('order_processing_seconds', 'Order processing time')

# Start metrics server
start_http_server(8000)
```

### Grafana Dashboard

Create dashboards to monitor:

- Message throughput
- Processing latency
- Error rates
- Consumer lag

### Logging

Configure structured logging:

```python
import logging
import json

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def log_event(event_type, **kwargs):
    log_data = {
        'timestamp': time.time(),
        'event_type': event_type,
        **kwargs
    }
    logging.info(json.dumps(log_data))
```

## Scaling Considerations

### Horizontal Scaling

- Increase number of producer/consumer instances
- Ensure proper partition assignment
- Monitor consumer lag

### Vertical Scaling

- Increase memory/CPU for data-intensive processing
- Tune JVM settings for Kafka clients
- Optimize batch sizes

### Auto-scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fulfillment-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fulfillment-service
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Security

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kafka-demo-policy
spec:
  podSelector:
    matchLabels:
      app: kafka-demo
  policyTypes:
    - Ingress
    - Egress
  egress:
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 9092 # Kafka
        - protocol: TCP
          port: 443 # HTTPS
```

### Pod Security Standards

```yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1001
    fsGroup: 1001
  containers:
    - name: kafka-demo
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
```

## Troubleshooting

### Common Deployment Issues

1. **Image pull errors** - Check registry credentials
2. **Config mount failures** - Verify ConfigMap/Secret names
3. **Network connectivity** - Check security groups/firewall rules
4. **Resource limits** - Monitor CPU/memory usage

### Health Checks

```python
# Add health check endpoint
from flask import Flask
app = Flask(__name__)

@app.route('/health')
def health_check():
    # Check Kafka connectivity
    # Check schema registry
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```
