
import json
import os
import pandas as pd
from utils import hash_text


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

    def add_line_json(self, file, content):
        anno_dict = self.read_json(file)
        if content[0] in anno_dict.keys():
            #update_val = anno_dict[content[0]]
            #update_val.append(content[1])
            if content[1] in anno_dict[content[0]]:
                anno_dict[content[0]].remove(content[1])
            else:
                anno_dict[content[0]].append(content[1])
        else:
            anno_dict[content[0]] = [content[1]]
        self.write_json(file, anno_dict)



class DataSet():
    def __init__(self, file, data_path):
        self.cm_d = FileManager(f'{data_path}/datasets/')
        self.cm_a = FileManager(f'{data_path}/annotations/')
        self.file = file
        self.df_items = self.cm_d.read_csv(self.file+'.csv')
        self.annotations = self.cm_a.read_json(self.file+'_annotations.txt')

    def all(self):
        # Lists all points
        return [{'id':i,'title':t,'labels':self.annotations.get(hash_text(i),[]), 'hash_id': hash_text(i)} for i,t in zip(self.df_items.index,self.df_items['text'].values)]

    def annotate(self, idx, content):
        # annotates a datapoint
        self.cm_a.add_line_json(self.file+'_annotations.txt', [str(idx), content])
        self.annotations = self.cm_a.read_json(self.file+'_annotations.txt')
