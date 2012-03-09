'''
Created on Jan 11, 2012

@author: Nils Gehlenborg, Harvard Medical School, nils@hms.harvard.edu
'''

import simplejson
import copy
import ast

class GalaxyWorkflow( object ):
    '''
    classdocs
    '''

    def __init__(self, name, identifier ):
        '''
        Constructor
        '''
        self.name = name
        self.identifier = identifier
        self.inputs = []
        
    def __unicode__(self):
        return self.name + " (" + self.identifier + "): " + str( len( self.inputs ) ) + " inputs"      

                
    def add_input( self, workflow_input ):
        self.inputs.append( workflow_input )
        


class GalaxyWorkflowInput( object ):
    
    def __init__(self, name, identifier ):
        '''
        Constructor
        '''
        self.name = name
        self.identifier = identifier
        
    def __unicode__(self):
        return self.name + " (" + self.identifier + ")"        


# =========================================================================================================
# Helper functions 
# =========================================================================================================

def openWorkflow(in_file):   
    """
    Opens a workflow file 
    """     
    with open(in_file) as f:
        temp_data = simplejson.load(f)
    return temp_data;

def createBaseWorkflow(workflow_name):
    """
    # Creates base template workflow # 
    """
    base_dict = {};
    base_dict["a_galaxy_workflow"] = "true";
    base_dict["annotation"] = "";
    base_dict["format-version"] = "0.1"
    base_dict["name"] = workflow_name;
    base_dict["steps"] = {};
    return base_dict;

def workflowMap(workflow):
    """
    Returns a dict of mapped workflow
    
    """
    map = {};
    temp_steps = workflow["steps"];
    
    # finds input files ("exp_file" or "input_file") read from galaxy
    for j in range(0, len(temp_steps)):
        curr_workflow_step = temp_steps[str(j)]
        input_id = curr_workflow_step["id"]
        input_dict = curr_workflow_step["inputs"];
        
        if (len(input_dict) > 0):
            if input_dict[0]["name"] == 'exp_file':
                map[input_id] = 'exp';
            elif input_dict[0]["name"] == 'input_file':
                map[input_id] = 'input'
    
    # mapping rest of workflow to either "input_file" or "exp_file"
    for k in range(0, len(temp_steps)):
        curr_workflow_step = temp_steps[str(k)]
        input_id = curr_workflow_step["id"]
        connect_dict = curr_workflow_step["input_connections"];
        if (len(connect_dict)) == 1:
            for keys, val in connect_dict.iteritems():
                if "id" in connect_dict[keys]:
                    step_input_id = connect_dict[keys]['id'];
                    map[input_id] = map[step_input_id];
        elif (len(connect_dict)) > 1:
             map[input_id] = "all"
                    
    return map;

def removeFileExt(file_name):
    """
    function for removing file extension from filename
    i.e. returns "test" from "test.fastq" 
    """
    split_num = file_name.strip().split('.');
    if len(split_num) > 0:
        return split_num[0];
    else:
        return file_name;


def createStepsAnnot(file_list, workflow):
    #print "createStepsAnnot called"
    """
    Replicates an input dictionary : "X" number of times depending on value of repeat_num 
    """
    
    updated_dict = {};
    temp_steps = workflow["steps"];
    repeat_num = len(file_list);
    
    map = workflowMap(workflow);
    
    print "filelist"
    print file_list
    print len(file_list);
    
    for i in range(0, repeat_num):
        for j in range(0, len(temp_steps)):
            curr_id = str(len(temp_steps)*i+j);
            curr_step = str(j);
            curr_workflow_step = copy.deepcopy(temp_steps[curr_step])
            
            # 1. Update steps: id
            curr_workflow_step["id"] = int(curr_id);
            
            # 2. Update any connecting input_ids
            input_dict = curr_workflow_step["input_connections"];
            num_inputs = len(input_dict);
            if (input_dict):
                for key in input_dict.keys():
                    if input_dict[key]['id'] is not None:
                        input_id_old = input_dict[key]['id']
                        input_id_new = (len(temp_steps)*i+int(input_id_old));
                        input_dict[key]['id'] = input_id_new;
            
            # 3. Update positions 
            pos_dict = curr_workflow_step["position"];
            if pos_dict:
                top_pos = pos_dict["top"];
                left_pos = pos_dict["left"]
                # TODO: find a better way of defining positions 
                pos_dict["top"] = top_pos * (i+1);
           
           
            # 4. Updating post job actions for renaming datasets
            if (len(curr_workflow_step['inputs']) == 0):
                tool_name = curr_workflow_step["tool_id"];
                input_type = map[int(curr_step)];
                # getting current filename for workflow
                curr_filename = '';
                if (input_type == 'exp'):
                    curr_filename = removeFileExt(file_list[i]['exp']['filename']);
                elif (input_type == 'input'):
                    curr_filename = removeFileExt(file_list[i]['input']['filename']);
                else: 
                    curr_filename = removeFileExt(file_list[i]['exp']['filename']) + ',' + removeFileExt(file_list[i]['input']['filename']);
                
                
                # TODO: get list of ["outputs"]["name"]
                output_names = [];
                output_list = curr_workflow_step['outputs']
                if (len(output_list) > 0):
                    for ofiles in output_list:
                        output_names.append(ofiles['name']);
                
                # TODO: change post_job_actions: [RenameDatasetAction][newname] to newly generated (id + tool + filename)
                if "post_job_actions" in curr_workflow_step:
                    pja_dict = curr_workflow_step["post_job_actions"];
                    
                    for oname in output_names:
                        temp_key = 'RenameDatasetAction' + str(oname);
                        new_output_name = tool_name + ',' + input_type + ',' + str(oname) + ',' + curr_filename
                        
                        # if rename dataset action already exists for this tool output
                        if temp_key in pja_dict:
                            pja_dict[temp_key]['action_arguments']['newname'] = new_output_name;
                        # whether post_job_action,RenameDatasetAction exists or not
                        else:
                            #new_rename_action =  '{"%s": { "action_arguments": { "newname": "%s" }, "action_type": "RenameDatasetAction", "output_name": "%s"}}' % (temp_key, new_output_name, oname);
                            new_rename_action =  '{ "action_arguments": { "newname": "%s" }, "action_type": "RenameDatasetAction", "output_name": "%s"}' % (new_output_name, oname);
                            
                            new_rename_dict = ast.literal_eval(new_rename_action);
                            pja_dict[temp_key] = new_rename_dict;

            """
                #print pja_dict;
                for k, v in pja_dict.iteritems():
                    print "num_inputs"
                    print num_inputs;
                    
                    # If the post job actions contain a RenameDatasetAction
                    if "action_type" in v:
                        if v["action_type"] == 'RenameDatasetAction':
                            print "------"
                            print("Post Job Actions");
                            print("NAME: " + curr_workflow_step['name'])
                            print pja_dict;
                    
                            print k;
                            print v;
                            v["action_arguments"]["newname"] = v["action_arguments"]["newname"] + "_" + str(i+1);                
                            print v["action_arguments"]["newname"];
            """
                
                
                    
            """
            if 'RenameDatasetActionoutput_file' in pja_dict:
                    print pja_dict['RenameDatasetActionoutput_file']
                    print pja_dict['RenameDatasetActionoutput_file']['action_arguments']['newname']
                
            "post_job_actions": {
                "RenameDatasetActionoutput1": {
                    "action_arguments": {
                        "newname": "sam_to_bam_02"
                        }, 
                    "action_type": "RenameDatasetAction", 
                        "output_name": "output1"
                    }
                }
            """
            
            # Adds updated module 
            updated_dict[curr_id] = curr_workflow_step;
            
    return updated_dict;

def createSteps(repeat_num, workflow):
    #print "createSteps called"
    """
    Replicates an input dictionary : "X" number of times depending on value of repeat_num 
    """
    
    updated_dict = {};
    temp_steps = workflow["steps"];
    
    for i in range(0, repeat_num):
        for j in range(0, len(temp_steps)):
            curr_id = str(len(temp_steps)*i+j);
            curr_step = str(j);
            curr_workflow_step = copy.deepcopy(temp_steps[curr_step])
            
            # 1. Update steps: id
            curr_workflow_step["id"] = int(curr_id);
            
            # 2. Update any connecting input_ids
            input_dict = curr_workflow_step["input_connections"];
            if (input_dict):
                for key in input_dict.keys():
                    if input_dict[key]['id'] is not None:
                        input_id_old = input_dict[key]['id']
                        input_id_new = (len(temp_steps)*i+int(input_id_old));
                        input_dict[key]['id'] = input_id_new;
            
            # 3. Update positions 
            pos_dict = curr_workflow_step["position"];
            if pos_dict:
                top_pos = pos_dict["top"];
                left_pos = pos_dict["left"]
                # TODO: find a better way of defining positions 
                pos_dict["top"] = top_pos * (i+1);
            
            # Adds updated module 
            updated_dict[curr_id] = curr_workflow_step;
            
    return updated_dict;