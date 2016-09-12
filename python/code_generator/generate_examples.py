# -*- coding: utf-8 -*-
"""
    E-mail: quikeval@linear.com

    Copyright (c) 2016, Linear Technology Corp.(LTC)
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, 
       this list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright 
       notice, this list of conditions and the following disclaimer in the 
       documentation and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
    ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE 
    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
    POSSIBILITY OF SUCH DAMAGE.

    The views and conclusions contained in the software and documentation are 
    those of the authors and should not be interpreted as representing official
    policies, either expressed or implied, of Linear Technology Corp.

    Description:
        The purpose of this module is to generate the example code.
"""

import toml
import re
import datetime
import os

def replace_values(template, value_dict):
    for key, value in value_dict.iteritems():
        template = template.replace("?"+key+"?", str(value))
    template = template.replace("?year?", str(datetime.datetime.now().year))
    return template
        
def make_id_name(name):
    return re.sub("[^a-zA-Z0-9_]", "_", name)
    
def make_var_name(name):
    return make_id_name(name.lower())
    
def make_class_name(name):
    name = name[0].upper() + name[1:].lower()
    print "name is '" + name + "'"
    repl = lambda m: m.group(1).upper()
    name = re.sub("[- _]+([a-z])", repl, name)
    return re.sub("[^a-zA-Z0-9]", "", name)

def generate(template_file_name, toml_file_name, controller):
            
    with open(template_file_name) as template_file:
        template = template_file.read()

    with open(toml_file_name) as toml_file:
        instances = toml.loads(toml_file.read())
        
    for key, value in instances.iteritems():
        if value["controller"] == controller:
            func_name = make_var_name(key)
            out_file_name = func_name + ".py"
            class_name = make_class_name(value["dc_number"])
            value["func_name"] = func_name
            value["class_name"] = class_name
            
            instance = replace_values(template, value)
            folder = value["part_number"].lower()
            try:
                os.makedirs(folder)
            except:
                pass
            with open( folder + "/" + out_file_name, "wt") as out_file:
                out_file.write(instance)

if __name__ == "__main__":
    generate("dc718_template.txt", "demoboards.toml", 'DC718')
    #generate("dc890_template.txt", "demoboards.toml", 'DC890')
    #generate("dc1371_template.txt", "demoboards.toml", 'DC1371')
