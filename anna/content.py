
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

    def update_json(self, file, entry):
        anno_dict = self.read_json(file)
        anno_dict, outcome = update_annotation_item(anno_dict, entry)
        self.write_json(file, anno_dict)
        return outcome

def get_avg_index(idx_prev, idx_next = None):
    """
    Incremental index rows will have the format idx__ind_dec
    0001__0_512 will mean index position 0.512 after position 0001 
    """
    print(idx_prev, idx_next)
    idx_core = idx_prev.split('__')[0]
    if idx_next:
        assert(idx_core==idx_next.split('__')[0])
        idx_prev_loc = '0' if len(idx_prev.split('__'))==1 else idx_prev.split('__')[1]
        idx_prev_loc = float(idx_prev_loc.replace('_','.'))
        idx_next_loc = idx_next.split('__')[1]
        idx_next_loc = float(idx_next_loc.replace('_','.'))
        new_idx = sum([idx_prev_loc,idx_next_loc])/2
        i, d = divmod(new_idx, 1)
        res = f'{idx_core}__{int(i)}_{str(d)[2:10]}'
    else:
        if len(idx_prev.split('__'))==1:
            res = idx_core + '__1'
        else:
            res = idx_core + '__' + str(int(idx_prev.split('__')[1])+1)
            
    return res

def update_annotation_item(anno_dict, entry):
    """
    Amends the annotation with a new entry. Entry is a dictionary with 'id', 'type', 'value'
    

    returns:
        outcome - whether to increase / decrease counter
    """
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
        if ('remove_edits' in entry.keys()) and ('content' in anno_dict[entry['id']].keys()):
            del anno_dict[entry['id']]['content']
        # If this is a new row altogether, removing edit means, deleting the item
        elif ('remove_edits' in entry.keys()) and (len(entry['id'].split('__'))>1):
            del anno_dict[entry['id']]
        else:
            anno_dict[entry['id']][entry['type']] = [entry['value']]

        if entry['type'] not in ['comment','content']:
            outcome = 1
        # COMMENT no text now and there was text before (applies only to COMMENT because deleting the whole text is an edit)
        elif len(entry['value'])==0 and len_init_value>0 and entry['type'] == 'comment':
            outcome = -1
        elif 'content' not in anno_dict[entry['id']].keys() and len_init_value>0 and entry['type'] == 'content':
            outcome = -1
        # COMMENT there is text now and no text before
        elif len(entry['value'])>0 and len_init_value==0 and entry['type'] == 'comment':
            outcome = 1
        elif 'content' in anno_dict[entry['id']].keys() and len_init_value==0 and entry['type'] == 'content':
            outcome = 1
        # COMMENT and there was text before and there is text now OR there was no text and there is still no text
        else:
            outcome = 0
    return anno_dict, outcome

class DataSet():
    def __init__(self, file, data_path, config_name):
        self._read_config(config_name)
        self.cm_d = FileManager(f'{data_path}/datasets/')
        self.cm_a = FileManager(f'{data_path}/annotations/')
        self.file = file
        self.df_items = self.cm_d.read_csv(self.file)
        self.file_path_annotations =f"{self.file.replace('.csv','').replace('.txt','')}_{config_name}_annotations.txt"
        self.annotations = self.cm_a.read_json(self.file_path_annotations)
        
        self.added_lines_dict = {}
        for a in self.annotations:
            if len(a.split('__'))>1:
                if a.split('__')[0] in self.added_lines_dict:
                    self.added_lines_dict[a.split('__')[0]].append(a)
                else:
                    self.added_lines_dict[a.split('__')[0]] = [a]
        print('Added lines',self.added_lines_dict)

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

    def _get_content_edited_text(self,idx,field_name):
        return '; '.join(self.annotations.get(hash_text(idx),{}).get(field_name,[]))

    def _read_dataset_item(self, ii, idx, t, force_hash = None):
        if force_hash:
            hash_idx = force_hash
        else:
            hash_idx = hash_text(idx)
        content_edited_text = self._get_content_edited_text(idx,'content')
        content_value = t if len(content_edited_text)==0 else content_edited_text
        d = {
            'nr': ii,
            'id': idx,
            'content':content_value,
            'content_edited': True if len(content_edited_text)>0 else False,
            'labels': self.annotations.get(hash_idx,{}).get('labels',[]), 
            'comment': self._get_content_edited_text(idx,'comment'),
            'hash_id': hash_idx
        }
        return d, hash_idx

    def get_target(self, hash_idx):
        """Retrieve target content from original doc by hash_idx
        The raw doc still has its original index in column index_col
        We have a hash_idx to look for here so we need to loop through all items, hash them and check for match
        """
        if len(hash_idx.split('__'))>1:
            # Check if this is an item added by the creative
            target = ';'.join(self.annotations[hash_idx].get('content',['...']))
        else:
            for ii, idx in enumerate(self.df_items[self.index_col]):
                if hash_idx == hash_text(idx):
                    target = self.df_items[self.target].iloc[ii]
                    break
        return target

    def all(self):
        """Retrieve all items and prepare them to be shown on the page.
        Return data: list object which will be read out on the page
        """
        reserved_labels_in_use = any([c in self.labels_list for c in ['comment','content']])
        # Lists all points
        if (self.index_col in self.df_items.columns) and (self.target in self.df_items.columns) and (not reserved_labels_in_use):
            data = []
            d_idx = []
            #for lbl in self.labels:
            #    lbl['count'] = 0
            for ii, idx, t in zip(range(len(self.df_items)),self.df_items[self.index_col],self.df_items[self.target].values):
                d, hash_idx = self._read_dataset_item(ii, idx, t)
                data.append(d)
                d_idx.append(hash_idx)
                if hash_idx in self.added_lines_dict:
                    list_added_lines = self.added_lines_dict[hash_idx]
                    list_added_lines.sort()
                    for iii, hash_anno_idx in enumerate(list_added_lines):
                        t = self.get_target(hash_anno_idx)
                        d, hash_idx = self._read_dataset_item(f'{ii}_{iii}', '', t, hash_anno_idx)
                        data.append(d)    
                        d_idx.append(hash_idx)
                for lbl in self.labels:
                    lbl['count'] = lbl.get('count',0) + (1 if lbl['name'] in d['labels'] else 0)
                self.nr_comments = self.nr_comments + (1 if len(d['comment']) else 0)
                self.nr_edits = self.nr_edits + (1 if d['content_edited'] else 0)

        elif reserved_labels_in_use:
            data = [{
                    'nr': 0,
                    'id': 0,
                    'content':'NA: Config not allowed, label name "comment" and "content" not allowed',
                    'labels':[], 
                    'comment':'',
                    'hash_id': 'x'
                    }]
        else:
            data = [{
                    'nr': 0,
                    'id': 0,
                    'content':'NA: Data not compatible with this config',
                    'labels':[], 
                    'comment':'',
                    'hash_id': 'x'
                    }]
        return data

    def add_line(self, input_idx):
        core_idx = input_idx.split('__')[0]
        matched_core_idx_ls = [a for a in self.annotations if core_idx in a]
        matched_core_idx_ls.sort()
        # Assert input_idx is either same as core or in the added ones
        assert(any([core_idx == input_idx, input_idx in matched_core_idx_ls]))
        # Finding the next key: input_idx is the line we will add below. 
        # For input_idx there are two options: it is part of the original list (i.e. input_idx == core_idx) or it was added by the creative
        # In the latter case, it will be in the matched_core_idx_ls and we need to find the item after it, after sorting
        if core_idx == input_idx and len(matched_core_idx_ls)==0:
            # input_idx is in the original AND there are no added items to it yet
            next_idx = None
        elif core_idx == input_idx and len(matched_core_idx_ls)>0:
            next_idx = matched_core_idx_ls[0]
        else:
            position_in_matched = matched_core_idx_ls.index(input_idx)
            if position_in_matched+1 == len(matched_core_idx_ls):
                # This index is the last of the added ones
                next_idx = None
            else:
                next_idx = matched_core_idx_ls[position_in_matched+1]

        idx = get_avg_index(input_idx, idx_next = next_idx)
        content = '...'
        entry = {'id': str(idx), 'value':content, 'type':'content'}
        print(entry)
        outcome = self.cm_a.update_json(self.file_path_annotations, entry)
        self.annotations = self.cm_a.read_json(self.file_path_annotations)
        if core_idx in self.added_lines_dict:
            self.added_lines_dict[core_idx].append(idx)
        else:
            self.added_lines_dict[core_idx] = [idx]
        return outcome

    def check_surronding_lines(self, orig_idx):
        """Function will check for any added lines as part of the annotation. If there are 
        """
        hash_only_idx = orig_idx.split('_')[0]
        self.annotations.keys()

    def annotate(self, idx, content, label_type, remove_edits=False):
        # adds to annotations file: comment, content edits and labels
        entry = {'id': str(idx), 'value':content, 'type':label_type}
        if remove_edits:
            entry['remove_edits'] = True
            if len(idx.split('__'))>1:
                self.added_lines_dict[idx.split('__')[0]].remove(idx)
                if len(self.added_lines_dict[idx.split('__')[0]])==0:
                    del self.added_lines_dict[idx.split('__')[0]]
        outcome = self.cm_a.update_json(self.file_path_annotations, entry)
        self.annotations = self.cm_a.read_json(self.file_path_annotations)
        return outcome

