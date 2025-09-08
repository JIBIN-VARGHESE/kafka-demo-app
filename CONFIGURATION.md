# Configuration Guide

## Overview

This guide provides detailed configuration instructions for setting up the Kafka Demo App with your Confluent Cloud cluster.

## Prerequisites

### 1. Confluent Cloud Account

- Sign up at [Confluent Cloud](https://confluent.cloud)
- Create a Basic or Standard cluster
- Note your cluster's bootstrap servers

### 2. Schema Registry

- Enable Schema Registry in your cluster
- Note the Schema Registry URL and credentials

### 3. API Keys & OAuth Setup

You'll need to create OAuth applications for different service roles:

#### For Order Producer (grocery-producers pool)

- Client ID: Used for producing orders
- Client Secret: Keep secure
- Permissions: WRITE to `grocery.orders.v1`, Schema Registry access

#### For Fulfillment Service

- Consumer Client ID: For reading orders
- Consumer Client Secret: Keep secure
- Producer Client ID: For writing picklists
- Producer Client Secret: Keep secure
- Permissions: READ from `grocery.orders.v1`, WRITE to `grocery.picklist.v1`

#### For Picklist Consumer

- Client ID: For reading picklists
- Client Secret: Keep secure
- Permissions: READ from `grocery.picklist.v1`

## Configuration Files

### 1. order_producer.py

Replace these placeholder values:

```python
BOOTSTRAP_SERVERS = "pkc-xxxxx.region.provider.confluent.cloud:9092"
SCHEMA_REGISTRY_URL = "https://psrc-xxxxx.region.provider.confluent.cloud"
OAUTH_TOKEN_URL = "https://xxxxx.confluent.cloud/oauth/token"
CLIENT_SECRET = "your-producer-oauth-secret"
```

### 2. fulfillment_service.py

Replace these placeholder values:

```python
BOOTSTRAP_SERVERS = "pkc-xxxxx.region.provider.confluent.cloud:9092"
SCHEMA_REGISTRY_URL = "https://psrc-xxxxx.region.provider.confluent.cloud"
OAUTH_TOKEN_URL = "https://xxxxx.confluent.cloud/oauth/token"
CONSUMER_CLIENT_SECRET = "your-consumer-oauth-secret"
PRODUCER_CLIENT_SECRET = "your-producer-oauth-secret"
```

### 3. picklist_consumer.py

Replace these placeholder values:

```python
BOOTSTRAP_SERVERS = "pkc-xxxxx.region.provider.confluent.cloud:9092"
SCHEMA_REGISTRY_URL = "https://psrc-xxxxx.region.provider.confluent.cloud"
OAUTH_TOKEN_URL = "https://xxxxx.confluent.cloud/oauth/token"
CLIENT_SECRET = "your-consumer-oauth-secret"
```

## Topic Configuration

### Create Topics

Create these topics in your Confluent Cloud cluster:

#### grocery.orders.v1

```bash
Partitions: 3
Retention: 7 days
Cleanup Policy: delete
Min In-Sync Replicas: 2
```

#### grocery.picklist.v1

```bash
Partitions: 3
Retention: 7 days
Cleanup Policy: delete
Min In-Sync Replicas: 2
```

## Schema Registry Setup

The schemas will be automatically registered when you run the services. Ensure your OAuth clients have schema registry permissions:

- **Read access**: To deserialize messages
- **Write access**: To register new schema versions
- **Compatibility checking**: Set to BACKWARD for safe evolution

## RBAC Configuration

### Identity Pools

1. **grocery-producers**

   - Description: Order API services
   - Members: Producer OAuth client

2. **grocery-fulfillment**
   - Description: Fulfillment services
   - Members: Fulfillment OAuth clients

### Role Bindings

#### grocery-producers Pool

```yaml
- ResourceType: Topic
  ResourceName: grocery.orders.v1
  Permission: WRITE

- ResourceType: Subject
  ResourceName: grocery.orders.v1-value
  Permission: READ,WRITE
```

#### grocery-fulfillment Pool

```yaml
- ResourceType: Topic
  ResourceName: grocery.orders.v1
  Permission: READ

- ResourceType: Topic
  ResourceName: grocery.picklist.v1
  Permission: WRITE

- ResourceType: Subject
  ResourceName: grocery.orders.v1-value
  Permission: READ

- ResourceType: Subject
  ResourceName: grocery.picklist.v1-value
  Permission: READ,WRITE

- ResourceType: Group
  ResourceName: fulfillment-service-group
  Permission: READ
```

## Environment Variables (Optional)

For production deployments, use environment variables:

```bash
export KAFKA_BOOTSTRAP_SERVERS="pkc-xxxxx.region.provider.confluent.cloud:9092"
export SCHEMA_REGISTRY_URL="https://psrc-xxxxx.region.provider.confluent.cloud"
export OAUTH_TOKEN_URL="https://xxxxx.confluent.cloud/oauth/token"
export PRODUCER_CLIENT_SECRET="your-secret"
export CONSUMER_CLIENT_SECRET="your-secret"
```

Then modify your Python files to read from environment:

```python
import os
BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
CLIENT_SECRET = os.getenv('PRODUCER_CLIENT_SECRET')
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**

   - Verify OAuth client credentials
   - Check token endpoint URL
   - Ensure clients have proper permissions

2. **Schema Errors**

   - Verify schema registry URL and credentials
   - Check schema file paths
   - Ensure compatibility settings

3. **Connection Errors**
   - Verify bootstrap servers URL
   - Check network connectivity
   - Verify SSL/TLS settings

### Testing Connection

Test your configuration with this simple script:

```python
from confluent_kafka.admin import AdminClient

conf = {
    'bootstrap.servers': 'your-bootstrap-servers',
    'sasl.mechanisms': 'OAUTHBEARER',
    'security.protocol': 'SASL_SSL',
    'sasl.oauthbearer.client.id': 'your-client-id',
    'sasl.oauthbearer.client.secret': 'your-client-secret',
    'sasl.oauthbearer.token.endpoint.url': 'your-token-url'
}

admin = AdminClient(conf)
metadata = admin.list_topics(timeout=10)
print(f"Connected! Available topics: {list(metadata.topics.keys())}")
```

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** in production
3. **Rotate OAuth secrets** regularly
4. **Monitor access logs** for unusual activity
5. **Use least-privilege** RBAC policies
6. **Enable audit logging** in Confluent Cloud
