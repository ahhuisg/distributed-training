import os
import queue
import pickle

import requests
from flask import Flask
from flask import request
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)

num_of_workers = int(os.environ['NUMBER_OF_WORKERS'])
print('num_of_workers : ', num_of_workers)

base_gcs_bucket = os.environ['BASE_GCS_BUCKET']

base_read_url = f'https://storage.googleapis.com/{base_gcs_bucket}'
print('base_read_url: ', base_read_url)

base_write_url = f'https://www.googleapis.com/upload/storage/v1/b/{base_gcs_bucket}/o?uploadType=media&name='
print('base_write_url: ', base_write_url)

model_merge_module_str = os.environ['MODEL_MERGE_MODULE']
model_merge_func_str = os.environ['MODEL_MERGE_FUNCTION']
print('model_merge_module_str: ', model_merge_module_str)
print('model_merge_func_str: ', model_merge_func_str)

py_file = model_merge_module_str + '.py'
response = requests.get(f'{base_read_url}/{py_file}')
with open(py_file, 'wb') as f:
    f.write(response.content)

model_merge_function = getattr(__import__(model_merge_module_str), model_merge_func_str)
print('model_merge_function: ', model_merge_function)

q = queue.Queue()
model_q = queue.Queue()

for i in range(num_of_workers):
    train_data = f'{base_read_url}/data/train_{i}.pkl'
    label_data = f'{base_read_url}/data/label_{i}.pkl'
    q.put({'train': train_data, 'label': label_data})

@app.route("/")
def hello():
    return "Hello from Distributed Training!"

@app.route("/get-item")
def get_item():
    print('inside getitem')
    url = None
    try:
        url = q.get(timeout=3)
        print('training data info: ', url)
        return url
    except queue.Empty:
        print('Empty queue')
        return {'train': None, 'label': None, 'error': 'Empty Queue'}

    return {'train': None, 'label': None, 'error': 'Error'}

@app.route('/put-model', methods=['POST'])
def put_model():
    print('inside put model')
    m = pickle.loads(request.get_data())
    print(m)
    model_q.put(m)
    
    print('Queue length: ', len(model_q.queue))
    if len(model_q.queue) == num_of_workers:
        print('Start combining models')
        model_list = list(model_q.queue)
        model = model_merge_function(model_list)
        print('model:', model)
        model_q.queue.clear()

        url = base_write_url + 'combined_model.pkl'
        data = pickle.dumps(model,protocol=2)
        requests.post(url, data=data)
        print('Done post combined model to ', url)
    
    return 'Done'

if __name__ == "__main__":
    app.run(host='0.0.0.0')
