from flask import Flask,request,redirect,url_for,render_template
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from secret import secret_key

import json
from joblib import load

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



db = {}

@app.route('/graph', methods=['GET'])
@login_required
def graph():
    print('ciao',current_user.id)
    return redirect(url_for('static', filename='graph.html'))

@app.route('/graph2', methods=['GET'])
def graph2():
    print('ciao2')
    d2 = json.loads(get_data('s1')[0])
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
    return json.dumps(list(db.keys())), 200




@app.route('/sensors/<s>',methods=['POST'])
def add_data(s):
    data = request.values['data']
    val = float(request.values['val'])
    if s in db:
        db[s].append((data,val))
    else:
        db[s] = [(data,val)]
    return 'ok',200

@app.route('/sensors/<s>',methods=['GET'])
def get_data(s):
    if s in db:
        # return json.dumps(db[s])
        r = []
        for i in range(len(db[s])):
            r.append([i,db[s][i][1]])

        model = load('model.joblib')
        for i in range(10):
            yp = model.predict([[r[-1][1],r[-2][1],r[-3][1],0]])
            r.append([len(r),yp[0]])

        return json.dumps(r),200
    else:
        return 'sensor not found',404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
    print('ciao')

