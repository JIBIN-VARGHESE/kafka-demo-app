import time
import uuid
from confluent_kafka import DeserializingConsumer, SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
 
# ---------------- CONFIG ----------------
BOOTSTRAP_SERVERS = "<KAFKA_BOOTSTRAP_SERVERS>"
SCHEMA_REGISTRY_URL = "<SCHEMA_REGISTRY_URL>"
OAUTH_TOKEN_URL = "<OAUTH_TOKEN_URL>"
 
# Consumer OAuth credentials
CONSUMER_CLIENT_ID = "70526360-cab9-410d-82b4-218d547203f4"
CONSUMER_CLIENT_SECRET = "<CONSUMER_CLIENT_SECRET>"
 
# Producer OAuth credentials
PRODUCER_CLIENT_ID = "4ac804a3-7edc-4212-95e2-22cca34a11c1"
PRODUCER_CLIENT_SECRET = "<PRODUCER_CLIENT_SECRET>"
 
ORDERS_TOPIC = "grocery.orders.v1"
PICKLIST_TOPIC = "grocery.picklist.v1"
GROUP_ID = "fulfillment-service-group"
 
# ---------------- SCHEMA SETUP ----------------
schema_registry_conf = {
    "url": SCHEMA_REGISTRY_URL,
    "basic.auth.user.info": f"{PRODUCER_CLIENT_ID}:{PRODUCER_CLIENT_SECRET}"
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
 
with open("schemas/grocery_orders.avsc") as f:
    order_schema_str = f.read()
 
with open("schemas/grocery_picklist.avsc") as f:
    picklist_schema_str = f.read()
 
order_deserializer = AvroDeserializer(schema_registry_client, order_schema_str)
picklist_serializer = AvroSerializer(schema_registry_client, picklist_schema_str)
 
# ---------------- CONSUMER ----------------
consumer_conf = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "sasl.mechanisms": "OAUTHBEARER",
    "security.protocol": "SASL_SSL",
    "sasl.oauthbearer.client.id": CONSUMER_CLIENT_ID,
    "sasl.oauthbearer.client.secret": CONSUMER_CLIENT_SECRET,
    "sasl.oauthbearer.token.endpoint.url": OAUTH_TOKEN_URL,
    "key.deserializer": str,
    "value.deserializer": order_deserializer,
    "group.id": GROUP_ID,
    "auto.offset.reset": "earliest"
}
consumer = DeserializingConsumer(consumer_conf)
consumer.subscribe([ORDERS_TOPIC])
 
# ---------------- PRODUCER ----------------
producer_conf = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "sasl.mechanisms": "OAUTHBEARER",
    "security.protocol": "SASL_SSL",
    "sasl.oauthbearer.client.id": PRODUCER_CLIENT_ID,
    "sasl.oauthbearer.client.secret": PRODUCER_CLIENT_SECRET,
    "sasl.oauthbearer.token.endpoint.url": OAUTH_TOKEN_URL,
    "key.serializer": str.encode,
    "value.serializer": picklist_serializer,
}
producer = SerializingProducer(producer_conf)
 
# ---------------- FULFILLMENT LOGIC ----------------
def process_orders():
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
 
        order = msg.value()
        picklist = {
            "picklist_id": str(uuid.uuid4()),
            "order_id": order["order_id"],
            "items_to_pick": order["items"],
            "assigned_picker": "picker-123",
            "created_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
 
        producer.produce(topic=PICKLIST_TOPIC, key=picklist["picklist_id"], value=picklist)
        producer.flush()
        print(f"Processed order {order['order_id']} -> Picklist {picklist}")
 
if __name__ == "__main__":
    process_orders()
 