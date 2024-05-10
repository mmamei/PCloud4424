
import time
import json
from google.cloud import pubsub_v1
from google.auth import jwt

sensor = 's2'


service_account_info = json.load(open("credentials.json"))
audience = "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
credentials = jwt.Credentials.from_service_account_info(
    service_account_info, audience=audience
)
publisher = pubsub_v1.PublisherClient(credentials=credentials)
topic_path = publisher.topic_path('pcloud2024-2', 'test-topic')

try:
    topic = publisher.create_topic(request={"name": topic_path})
    print(f"Created topic: {topic.name}")
except Exception as e:
    print(e)


with open('CleanData_PM10.csv') as f:
    for l in f.readlines()[1:]:
        data,val = l.strip().split(',')
        print(data,val)

        r = publisher.publish(topic_path, b'save', s=sensor, data=data, val=val)
        time.sleep(5)


print('done')
