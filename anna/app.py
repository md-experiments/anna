from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import json
import yaml
from utils import read_yaml
from content import FileManager, DataSet

app = Flask(__name__)

data_path = './data'

configs = read_yaml('./config.yaml')
list_configs = list(configs.keys())

@app.route("/annotate/<string:config_name>/<string:file_name>")
def home(file_name,config_name):
    list_files = ['joe_rogan_1169_elon_musk_transcript','john','alex']
    ds = DataSet(file_name, data_path, config_name)
    ds_list = ds.all()
    return render_template("base.html", list_files=list_files, 
            data_list=ds_list, file_name = file_name, labels = ds.labels, config_name = config_name, list_configs = list_configs)

@app.route("/update/<string:config_name>/<string:file_name>/<string:label_name>/<string:dp_id>")
def update(label_name, dp_id, file_name, config_name):
    DataSet(file_name, data_path, config_name).annotate(idx=dp_id,content = label_name)
    return redirect(f"/annotate/{config_name}/{file_name}#{dp_id}")


if __name__ == "__main__":

    app.run(debug=True)