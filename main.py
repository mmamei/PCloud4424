from flask import Flask,request,redirect,url_for,render_template
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from secret import secret_key
from google.cloud import firestore
import json
from joblib import load
from google.cloud import storage
from google.cloud import pubsub_v1
from google.auth import jwt

class User(UserMixin):
    def __init__(self, username):
        super().__init__()
        self.id = username
        self.username = username

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
login = LoginManager(app)
login.login_view = '/static/login.html'

usersdb = {
    'marco':'mamei'
}

@login.user_loader
def load_user(username):
    if username in usersdb:
        return User(username)
    return None

@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('/sensors'))
    username = request.values['u']
    password = request.values['p']
    if username in usersdb and password == usersdb[username]:
        login_user(User(username))
        return redirect('/sensors')
    return redirect('/static/login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


db = 'sensors'
coll = 'data'
db = firestore.Client.from_service_account_json('credentials.json', database=db)
#db = firestore.Client(database=db)


@app.route('/graph', methods=['GET'])
@login_required
def graph():
    print('ciao',current_user.id)
    return redirect(url_for('static', filename='graph.html'))

@app.route('/graph2/<s>', methods=['GET'])
def graph2(s):
    print('ciao2')
    d2 = json.loads(get_data(s)[0])
    ds = '' # ['2004',  1000,      null],
    for x in d2[:-10]:
        ds += f"['{x[0]}',{x[1]},null],\n"
    for x in d2[-10:]:
        ds += f"['{x[0]}',null, {x[1]}],\n"
    print(ds)


    return render_template('graph.html',data=ds)

@app.route('/',methods=['GET'])
def main():
    return sensors()

@app.route('/sensors',methods=['GET'])
def sensors():
    s = []
    for entity in db.collection(coll).stream():  # select * from sensor2
        s.append(entity.id)
    return json.dumps(s), 200



@app.route('/sensors/<s>',methods=['POST'])
def add_data_http(s):
    data = request.values['data']
    val = float(request.values['val'])
    store_data(s,data,val)
    return 'done'

@app.route('/sensors/pubsub',methods=['POST'])
def add_data_pubsub():
    dict = json.loads(request.data.decode('utf-8'))  # deserializzazione
    print('**********************')

    '''
    {'message': 
    {'attributes': {'d': '2020-01-07 00:00:00', 's': 's2', 'val': '18.0'}, 
    'data': 'c2F2ZQ==', 
    'messageId': '11037274795654212', 
    'message_id': '11037274795654212', 
    'publishTime': '2024-05-10T14:01:44.932Z', 
    'publish_time': '2024-05-10T14:01:44.932Z'}, 
    'subscription': 'projects/pcloud2024-2/subscriptions/push_sub_v2'}
    '''

    print(dict)
    s = dict['message']['attributes']['s']
    data = dict['message']['attributes']['d']
    val = float(dict['message']['attributes']['val'])
    store_data(s,data,val)

def store_data(s,data,val):
    doc_ref = db.collection(coll).document(s)
    if doc_ref.get().exists:
        # update
        diz = doc_ref.get().to_dict()['values']
        diz[data] = val
        doc_ref.update({'values': diz})
    else:
        doc_ref.set({'values': {data:val}})
    return 'ok',200




@app.route('/sensors/<s>',methods=['GET'])
def get_data(s):
    doc_ref = db.collection(coll).document(s)
    if doc_ref.get().exists:
        r = []
        diz = doc_ref.get().to_dict()['values']
        #diz = sorted(diz)

        i = 0
        for k,v in diz.items():
            r.append([i,v])
            i += 1

        storage_client = storage.Client.from_service_account_json('credentials.json')
        #storage_client = storage.Client()
        bucket = storage_client.bucket('pcloud2024-models')
        blob = bucket.blob('model.joblib')
        blob.download_to_filename('/tmp/model.joblib')
        model = load('/tmp/model.joblib')

        yp = model.predict([[r[-2][1], r[-3][1], r[-4][1], 0]])
        if abs(yp - r[-1][1]) > 10:
            send_retrain_req()

        for i in range(10):
            yp = model.predict([[r[-1][1],r[-2][1],r[-3][1],0]])
            r.append([len(r),yp[0]])



        return json.dumps(r),200
    else:
        return 'sensor not found',404


def send_retrain_req():
    print('send retrain')
    service_account_info = json.load(open("credentials.json"))
    audience = "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
    credentials = jwt.Credentials.from_service_account_info(service_account_info, audience=audience)
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
    topic_path = publisher.topic_path('pcloud2024-2', 'retrainreq')
    r = publisher.publish(topic_path, b'retrain!')
    print(r.result())



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
    print('ciao')

