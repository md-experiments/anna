from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import json
import yaml

from content import FileManager, DataSet

app = Flask(__name__)

data_path = './data'

with open('./config.yaml') as file:
    read_configs = yaml.load(file, Loader=yaml.FullLoader)

config = read_configs['bob']

button_colors =['primary','secondary','success','warning','info','light']
labels =[
    {'name':lbl.lower(),'title':lbl,'button_style':button_colors[i]} for i,lbl in enumerate(config['labels_config'])
]



@app.route("/annotate/<string:file_name>")
def home(file_name):
    list_files = [{'name':'bob'},{'name':'john'},{'name':'alex'}]
    ds = DataSet(file_name, data_path).all()
    return render_template("base.html", list_files=list_files, data_list=ds, file_name = file_name, labels = labels)

@app.route("/update/<string:file_name>/<string:label_name>/<string:dp_id>")
def update(label_name, dp_id, file_name):
    DataSet(file_name, data_path).annotate(idx=dp_id,content = label_name)

    return redirect(f"/annotate/{file_name}")


if __name__ == "__main__":

    app.run(debug=True)