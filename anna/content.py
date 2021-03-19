
import json
import os
import pandas as pd
from utils import hash_text, read_yaml
import yaml

class FileManager():
    def __init__(self, path):
        self.path = path
        
    def read_json(self,file):
        if os.path.exists(os.path.join(self.path,file)):
            with open(os.path.join(self.path,file),'r') as f:
                anno_dict = json.load(f)
        else:
            anno_dict = {}
        return anno_dict

    def write_json(self, file, content):
        with open(os.path.join(self.path,file),'w') as f:
            json.dump(content,f)

    def read_csv(self,file):
        if os.path.exists(os.path.join(self.path,file)):
            df = pd.read_csv(os.path.join(self.path,file),index_col=0)
        else:
            df = pd.DataFrame([])
        return df

    def add_line_json(self, file, entry):
        anno_dict = self.read_json(file)
        if entry['id'] not in anno_dict.keys():
            anno_dict[entry['id']] = {}

        if entry['type'] in anno_dict[entry['id']] and entry['type']!='comment':
            #update_val = anno_dict[content[0]]
            #update_val.append(content[1])
            if entry['value'] in anno_dict[entry['id']][entry['type']]:
                anno_dict[entry['id']][entry['type']].remove(entry['value'])
            else:
                anno_dict[entry['id']][entry['type']].append(entry['value'])
        else:
            anno_dict[entry['id']][entry['type']] = [entry['value']]
        self.write_json(file, anno_dict)



class DataSet():
    def __init__(self, file, data_path, config_name):
        self._read_config(config_name)
        self.cm_d = FileManager(f'{data_path}/datasets/')
        self.cm_a = FileManager(f'{data_path}/annotations/')
        self.file = file
        self.df_items = self.cm_d.read_csv(self.file)
        self.file_path_annotations =f"{self.file.replace('.csv','').replace('.txt','')}_{config_name}_annotations.txt"
        self.annotations = self.cm_a.read_json(self.file_path_annotations)

    def all(self):
        # Lists all points
        if (self.index_col in self.df_items.columns) and (self.target in self.df_items.columns):
            return [{
                'id':i,
                'title':t,
                'labels':self.annotations.get(hash_text(i),{}).get('labels',[]), 
                'comment':'; '.join(self.annotations.get(hash_text(i),{}).get('comment','')),
                'hash_id': hash_text(i)
                } 
                    for i,t in zip(self.df_items[self.index_col],self.df_items[self.target].values)]
        else:
            return []

    def annotate(self, idx, content,label_type):
        # annotates a datapoint
        entry = {'id':str(idx), 'value':content,'type':label_type}
        self.cm_a.add_line_json(self.file_path_annotations, entry)
        self.annotations = self.cm_a.read_json(self.file_path_annotations)

    def _read_config(self,config_name):
        read_configs = read_yaml('./config.yaml')
        config = read_configs[config_name]

        button_colors =['primary','secondary','success','warning','info','light']
        self.labels =[
            {'name':lbl.lower(),'title':lbl,'button_style':button_colors[i]} for i,lbl in enumerate(config['labels_config'])
        ]
        self.index_col = config['index_cols']
        self.target = config['target']