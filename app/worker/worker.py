import os
import time
import pickle
import importlib
import json

import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn import datasets
from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    print('inside worker')
    master_service = os.environ['MASTER_SERVICE']
    print('master_service: ', master_service)

    model_module = os.environ['MODEL_MODULE']
    model_class = os.environ['MODEL_CLASS']
    model_param_str = os.environ['MODEL_PARAMETERS']
    print('model_module: ', model_module)
    print('model_class: ', model_class)
    print('model_param_str: ', model_param_str)
    
    model_params_list = model_param_str.split(',')
    model_params = {}
    for param_str in model_params_list:
        param = param_str.split('=')
        model_params[param[0].strip()] = int(param[1])
    print('model_params: ', model_params)
    
    model_class = getattr(importlib.import_module(model_module), model_class)
    model = model_class(**model_params)
    print('model: ', model)

    #time.sleep(10)

    print('After sleep 10 seconds')
    get_item_url = "http://"+master_service + ":5000/get-item"
    print('Getting item ', get_item_url)
   
    data_url_dict = json.loads(requests.get(get_item_url).content)
    print('data_url_dict: ', data_url_dict)

    if 'error' not in data_url_dict:
        train_data_url = data_url_dict['train']
        label_data_url = data_url_dict['label']
        train_data_pkl = requests.get(train_data_url).content
        label_data_pkl = requests.get(label_data_url).content

        X = pickle.loads(train_data_pkl)
        y = pickle.loads(label_data_pkl)
        print('X.shape: ', X.shape)
        print('y.shape: ', y.shape)

        model.fit(X, y)
        print('Dumping model into pickle file')
        data = pickle.dumps(model,protocol=2)

        url = "http://"+master_service + ":5000/put-model"
        print('posting pickle file to ', url)
        r = requests.post(url,data=data)
        print('response: ', r)

    app.run(host='0.0.0.0', port=5001)

