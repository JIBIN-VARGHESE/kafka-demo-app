import time
import uuid
import random
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
 
# ---------------- CONFIG ----------------
BOOTSTRAP_SERVERS = "<KAFKA_BOOTSTRAP_SERVERS>"
SCHEMA_REGISTRY_URL = "<SCHEMA_REGISTRY_URL>"
OAUTH_TOKEN_URL = "<OAUTH_TOKEN_URL>"
CLIENT_ID = "4ac804a3-7edc-4212-95e2-22cca34a11c1"
CLIENT_SECRET = "<OAUTH_CLIENT_SECRET>"
TOPIC = "grocery.orders.v1"
 
# ---------------- SCHEMA SETUP ----------------
schema_registry_conf = {
    "url": SCHEMA_REGISTRY_URL,
    "basic.auth.user.info": f"{CLIENT_ID}:{CLIENT_SECRET}"
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
 
with open("schemas/grocery_orders.avsc") as f:
    order_schema_str = f.read()
 
order_serializer = AvroSerializer(schema_registry_client, order_schema_str)
 
# ---------------- PRODUCER ----------------
producer_conf = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "sasl.mechanisms": "OAUTHBEARER",
    "security.protocol": "SASL_SSL",
    "sasl.oauthbearer.client.id": CLIENT_ID,
    "sasl.oauthbearer.client.secret": CLIENT_SECRET,
    "sasl.oauthbearer.token.endpoint.url": OAUTH_TOKEN_URL,
    "key.serializer": str.encode,
    "value.serializer": order_serializer,
}
producer = SerializingProducer(producer_conf)
 
# ---------------- PRODUCE MESSAGE ----------------
def produce_orders():
    items = ["apple", "banana", "milk", "bread", "cheese"]
    while True:
        order = {
            "order_id": str(uuid.uuid4()),
            "customer_id": str(random.randint(1000, 9999)),
            "items": random.sample(items, k=random.randint(1, 3)),
            "order_total": round(random.uniform(10, 100), 2),
            "order_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        producer.produce(topic=TOPIC, key=order["order_id"], value=order)
        producer.flush()
        print(f"Produced order: {order}")
        time.sleep(2)
 
if __name__ == "__main__":
    produce_orders()
 