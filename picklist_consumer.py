from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
 
# ---------------- CONFIG ----------------
BOOTSTRAP_SERVERS = "<KAFKA_BOOTSTRAP_SERVERS>"
SCHEMA_REGISTRY_URL = "<SCHEMA_REGISTRY_URL>"
OAUTH_TOKEN_URL = "<OAUTH_TOKEN_URL>"
CLIENT_ID = "70526360-cab9-410d-82b4-218d547203f4"
CLIENT_SECRET = "<OAUTH_CLIENT_SECRET>"
TOPIC = "grocery.picklist.v1"
GROUP_ID = "picklist-consumer-group"
 
# ---------------- SCHEMA SETUP ----------------
schema_registry_conf = {
    "url": SCHEMA_REGISTRY_URL,
    "basic.auth.user.info": f"{CLIENT_ID}:{CLIENT_SECRET}"
}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
 
with open("schemas/grocery_picklist.avsc") as f:
    picklist_schema_str = f.read()
 
picklist_deserializer = AvroDeserializer(schema_registry_client, picklist_schema_str)
 
# ---------------- CONSUMER ----------------
consumer_conf = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,
    "sasl.mechanisms": "OAUTHBEARER",
    "security.protocol": "SASL_SSL",
    "sasl.oauthbearer.client.id": CLIENT_ID,
    "sasl.oauthbearer.client.secret": CLIENT_SECRET,
    "sasl.oauthbearer.token.endpoint.url": OAUTH_TOKEN_URL,
    "key.deserializer": str,
    "value.deserializer": picklist_deserializer,
    "group.id": GROUP_ID,
    "auto.offset.reset": "earliest"
}
consumer = DeserializingConsumer(consumer_conf)
consumer.subscribe([TOPIC])
 
# ---------------- READ PICKLIST ----------------
def consume_picklists():
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
 
        picklist = msg.value()
        print(f"Consumed picklist: {picklist}")
 
if __name__ == "__main__":
    consume_picklists()