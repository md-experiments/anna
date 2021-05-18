from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import json
import yaml
from utils import read_yaml, files_in_dir
from content import FileManager, DataSet, get_global_vars

app = Flask(__name__)

data_path = '../../endeavor/text_structure_extract/data'
#list_configs, list_files = get_global_vars(data_path)

@app.route("/")
def home0():
    # Load list_files and list_configs as global variables
    list_configs, list_files = get_global_vars(data_path)

    # Default values for intro screen
    file_name = 'alex.csv'
    config_name = 'example'
    ds = DataSet(file_name, data_path, config_name)
    ds_list = ds.all()
    return render_template("base.html", list_files=list_files, 
            data_list=ds_list, file_name = file_name, labels = ds.labels, 
            config_name = config_name, list_configs = list_configs, 
            nr_comments = ds.nr_comments, nr_edits = ds.nr_edits, editable_text = True)

@app.route("/annotate/<string:config_name>/<string:file_name>")
def home(file_name,config_name):
    list_configs, list_files = get_global_vars(data_path)
    ds = DataSet(file_name, data_path, config_name)
    ds_list = ds.all()
    pd.DataFrame(ds_list).to_csv(os.path.join(data_path,'annotations_latest',f'{file_name}_{config_name}_latest.csv'))
    return render_template("base.html", list_files=list_files, 
            data_list=ds_list, file_name = file_name, labels = ds.labels, 
            config_name = config_name, list_configs = list_configs, 
            nr_comments = ds.nr_comments, nr_edits = ds.nr_edits, editable_text = True)


@app.route("/<string:label_type>/<string:config_name>/<string:file_name>/<string:label_name>/<string:dp_id>", methods=['POST'])
def update(label_name, dp_id, file_name, config_name, label_type):
    received_url = request.form['url']
    received_label_name = request.form['label_name']
    label_title = request.form['label_title'].strip()

    if 'outline' in received_label_name:
        received_label_name = received_label_name.replace('outline-','')
    else:
        received_label_name = received_label_name.replace('btn-','btn-outline-')
    outcome = DataSet(file_name, data_path, config_name).annotate(idx = dp_id, content = label_name, label_type = label_type)
    #return redirect(f"/annotate/{config_name}/{file_name}#{dp_id}")
    
    data = {
        'name':f'button[name="{received_url}"]',
        'class':f'btn btn-{received_label_name}',
        'label_title':label_title,
        'outcome': outcome
    }
    print(outcome)
    return data

### ADDING COMMENTS
@app.route("/comment/<string:config_name>/<string:file_name>/<string:dp_id>", methods=['POST'])
def add_comment(dp_id, file_name, config_name):
    comment = request.form.get("comment_field")
    outcome = DataSet(file_name, data_path, config_name).annotate(idx = dp_id, content = comment, label_type = 'comment')
    #return redirect(f"/annotate/{config_name}/{file_name}#{dp_id}")
    return {
        'outcome': outcome
        }

### CONTENT EDITING - EDIT
@app.route("/content_edits/<string:config_name>/<string:file_name>/<string:dp_id>", methods=['POST'])
def edit_text(dp_id, file_name, config_name):
    comment = request.form.get("comment_field").strip()
    received_url = request.form['url']
    new_url = received_url.replace('content_edits','remove_edits')

    outcome = DataSet(file_name, data_path, config_name).annotate(idx = dp_id, content = comment, label_type = 'content')
    print(outcome)
    #return redirect(f"/annotate/{config_name}/{file_name}#{dp_id}")
    return {
       'outcome': outcome,
       'name': f'badge[name="{received_url}"]',
       'class': "badge bg-info",
       'new_url': new_url
        }

### CONTENT EDITING - RESET EDIT
@app.route("/remove_edits/<string:config_name>/<string:file_name>/<string:dp_id>", methods=['POST'])
def remove_edits(dp_id, file_name, config_name):
    received_url = request.form['url']
    new_url = received_url.replace('remove_edits','content_edits')

    ds = DataSet(file_name, data_path, config_name)
    outcome = ds.annotate(idx = dp_id, content = '', label_type = 'content', remove_edits = True)
    print(outcome)
    original_content = ds.get_target(dp_id)
    #return redirect(f"/annotate/{config_name}/{file_name}#{dp_id}")
    return {
        'outcome': outcome,
        'name': f'badge[name="{received_url}"]',
        'original_content': original_content,
        'class': "badge badge-transparent",
        'new_url': new_url
        }

### ADD LINE
@app.route("/add_line/<string:config_name>/<string:file_name>/<string:dp_id>")
def add_line(dp_id, file_name, config_name):
    list_configs, list_files = get_global_vars(data_path)
    ds = DataSet(file_name, data_path, config_name)
    ds.add_line(dp_id)
    ds_list = ds.all()
    return render_template("base.html", list_files=list_files, 
            data_list=ds_list, file_name = file_name, labels = ds.labels, 
            config_name = config_name, list_configs = list_configs, 
            nr_comments = ds.nr_comments, nr_edits = ds.nr_edits, editable_text = True)

if __name__ == "__main__":

    app.run(debug=True)