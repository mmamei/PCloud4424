'''import datetime
s = '2020-01-02 00:00:00'
d = datetime.datetime.strptime(s,'%Y-%m-%d %H:%M:%S')
print(d.timestamp() * 1000)
'''

from joblib import load

model = load('model.joblib')
#yp = model.predict(test.loc[:, ['PM10-1', 'PM10-2', 'PM10-3', 'weekend01']])
yp = model.predict([[34,45,55,0]])
print(yp[0])