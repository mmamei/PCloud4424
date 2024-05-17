from requests import get, post
import time

#base_url = 'http://34.154.202.65:80'
base_url = 'http://localhost'
#base_url = 'https://pcloud2024-2.ew.r.appspot.com'
sensor = 's1'
with open('CleanData_PM10.csv') as f:
    for l in f.readlines()[1:]:
        data,val = l.strip().split(',')
        print(data,val)
        r = post(f'{base_url}/sensors/{sensor}',
                 data={'data':data,'val':val})
        time.sleep(1)


print('done')
