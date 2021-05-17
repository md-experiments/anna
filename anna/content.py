
import json
import os
import pandas as pd
from utils import hash_text, read_yaml, files_in_dir
import yaml

def get_global_vars(data_path):
    configs = read_yaml('./config.yaml')
    list_configs = list(configs.keys())
    list_configs.sort()
    dataset_path = f'{data_path}/datasets/'
    list_files = files_in_dir(dataset_path)
    list_files = [f.split(dataset_path)[1] for f in list_files if not f.endswith('DS_Store')]
    list_files.sort()
    return list_configs, list_files

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
        """
        Amends the file with a new entry. Entry is a dictionary with 'id', 'type', 'value'
        

        returns:
            outcome - whether to increase / decrease counter
        """
        anno_dict = self.read_json(file)
        if entry['id'] not in anno_dict.keys():
            anno_dict[entry['id']] = {}

        # Updates label values THAT HAVE LABELS ALREADY - a list of labels selected (if a label is unselected -> it will be removed from the list)
        ## NB: label names cannot be 'comment' or 'content'
        if entry['type'] in anno_dict[entry['id']] and entry['type'] not in ['comment','content']:  
            if entry['value'] in anno_dict[entry['id']][entry['type']]:
                anno_dict[entry['id']][entry['type']].remove(entry['value'])
                outcome = -1
            else:
                anno_dict[entry['id']][entry['type']].append(entry['value'])
                outcome = 1
        # Updates COMMENT / CONTENT values or LABELS that are new
        else:
            if entry['type'] == 'comment':
                len_init_value = len(''.join(anno_dict[entry['id']].get(entry['type'],'')))
            elif entry['type'] == 'content':
                # In case of comment value can be edited to empty (ie line can be removed completely where there was text initially)
                if 'content' in anno_dict[entry['id']].keys():
                    len_init_value = 1
                else:
                    len_init_value = 0

            # Edits can be created, updated or removed
            if ('remove_edits' in anno_dict[entry['id']].keys()) and ('content' in anno_dict[entry['id']].keys()):
                del anno_dict[entry['id']]['content']
            else:
                anno_dict[entry['id']][entry['type']] = [entry['value']]
            if entry['type'] not in ['comment','content']:
                outcome = 1
            # COMMENT no text now and there was text before
            elif len(entry['value'])==0 and len_init_value>0:
                outcome = -1
            # COMMENT there is text now and no text before
            elif len(entry['value'])>0 and len_init_value==0:
                outcome = 1
            # COMMENT and there was text before and there is text now OR there was no text and there is still no text
            else:
                outcome = 0
        self.write_json(file, anno_dict)
        return outcome



class DataSet():
    def __init__(self, file, data_path, config_name):
        self._read_config(config_name)
        self.cm_d = FileManager(f'{data_path}/datasets/')
        self.cm_a = FileManager(f'{data_path}/annotations/')
        self.file = file
        self.df_items = self.cm_d.read_csv(self.file)
        self.file_path_annotations =f"{self.file.replace('.csv','').replace('.txt','')}_{config_name}_annotations.txt"
        self.annotations = self.cm_a.read_json(self.file_path_annotations)

    def _get_content_value(self,idx,field_name):
        return '; '.join(self.annotations.get(hash_text(idx),{}).get(field_name,[]))

    def _read_dataset_item(self, ii, idx, t):
        hash_idx = hash_text(idx)
        content_edited_text = self._get_content_value(idx,'content')
        content_value = t if len(content_edited_text)==0 else content_edited_text
        d = {
            'nr': ii,
            'id': idx,
            'content':content_value,
            'content_edited': True if len(content_edited_text)>0 else False,
            'labels': self.annotations.get(hash_idx,{}).get('labels',[]), 
            'comment': self._get_content_value(idx,'comment'),
            'hash_id': hash_idx
        }
        return d

    def all(self):
        reserved_labels_in_use = any([c in self.labels_list for c in ['comment','content']])
        # Lists all points
        if (self.index_col in self.df_items.columns) and (self.target in self.df_items.columns) and (not reserved_labels_in_use):
            data = []
            #for lbl in self.labels:
            #    lbl['count'] = 0
            for ii, idx, t in zip(range(len(self.df_items)),self.df_items[self.index_col],self.df_items[self.target].values):
                d = self._read_dataset_item(ii, idx, t)
                data.append(d)

                for lbl in self.labels:
                    lbl['count'] = lbl.get('count',0) + (1 if lbl['name'] in d['labels'] else 0)
                self.nr_comments = self.nr_comments + (1 if len(d['comment']) else 0)
                self.nr_edits = self.nr_edits + (1 if d['content_edited'] else 0)
            return data
        elif reserved_labels_in_use:
            return [{
                    'nr': 0,
                    'id': 0,
                    'content':'NA: Config not allowed, label name "comment" and "content" not allowed',
                    'labels':[], 
                    'comment':'',
                    'hash_id': 'x'
                    }]
        else:
            return [{
                    'nr': 0,
                    'id': 0,
                    'content':'NA: Data not compatible with this config',
                    'labels':[], 
                    'comment':'',
                    'hash_id': 'x'
                    }]

    def annotate(self, idx, content, label_type, remove_edits=False):
        # annotates a datapoint
        entry = {'id': str(idx), 'value':content, 'type':label_type}
        if remove_edits:
            entry['remove_edits'] = True
        outcome = self.cm_a.add_line_json(self.file_path_annotations, entry)
        self.annotations = self.cm_a.read_json(self.file_path_annotations)
        return outcome

    def _read_config(self,config_name):
        read_configs = read_yaml('./config.yaml')
        config = read_configs[config_name]

        button_colors =['primary','secondary','success','warning','info','light']
        self.labels =[
            {'name':lbl.lower(),'title':lbl,'button_style':button_colors[i], 'count': 0} for i,lbl in enumerate(config['labels_config'])
        ]
        self.labels_list = [lbl['name'] for lbl in self.labels]
        self.nr_comments = 0
        self.nr_edits = 0
        self.index_col = config['index_cols']
        self.target = config['target']
