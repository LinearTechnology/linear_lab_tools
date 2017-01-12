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

def replace_values(template, value_dict, is_matlab):
    for key, value in value_dict.iteritems():
        str_value = str(value)
        if is_matlab & isinstance(value, bool):
            str_value = str_value.lower()
        template = template.replace("?"+key+"?", str_value)
    return template
        
def make_id_name(name):
    return re.sub("[^a-zA-Z0-9_]", "_", name)
    
def make_var_name(name):
    return make_id_name(name.lower())
    
def make_class_name(name, keep_dash = False):
    name = name[0].upper() + name[1:].lower()
    print "name is '" + name + "'"
    repl = lambda m: m.group(1).upper()
    name = re.sub("[- _]+([a-z])", repl, name)
    if keep_dash:
        name = name.replace("-", "_")
        return re.sub("[^_a-zA-Z0-9]", "", name)
    return re.sub("[^a-zA-Z0-9]", "", name)

def make_function(string, is_matlab):
    func_name = make_var_name(string)
    ext = '.m' if is_matlab else '.py'
    return (func_name, func_name + ext)
    
def make_folder(part_number, is_matlab):
    name = part_number.lower()
    last_dash = name.rfind('-')
    if last_dash > 0:
        name = name[0:last_dash]
    if is_matlab:
        name = "+" + name
    return name

def split_and_strip(string):
    return map(str.strip, string.encode('utf-8').split(','))
        
def pair_up_items(a_list):
    return zip(a_list[0::2], a_list[1::2])

def get_space(key, template):
    m = re.search('( *)\?' + key + '\?', template)
    return m.group(1)

def format_spi_regs(spi_regs, template, is_matlab):
    space = get_space('spi_reg', template)
    if is_matlab:
        if len(spi_regs) == 0:
            return "... No SPI regs for this part."
        result = ''
        for address, value in pair_up_items(split_and_strip(spi_regs)):
            address = int(address, 16)
            value = int(value, 16)
            result += "{}hex2dec('{:0>2x}'), hex2dec('{:0>2x}'), ...\n".format(space, address, value)
        return result.strip()
    else:
        if len(spi_regs) == 0:
            return "# No SPI regs for this part."
        # join the items in each tuple with ', '; join the tuples with '\n'
        return (',\n' + space).join(map(', '.join, pair_up_items(split_and_strip(spi_regs))))
        
def make_dc1371_type(num_chip_selects, is_matlab):
    if num_chip_selects == 2:
        if is_matlab:
            return "Dc1371With2ChipSelects"
        else:
            return "Demoboard2ChipSelects"
    else:
        if is_matlab:
            return "Dc1371"
        else:
            return "Demoboard"

def generate(template_file_name, toml_file_name, controller, is_matlab=False):
            
    with open(template_file_name) as template_file:
        template = template_file.read()

    with open(toml_file_name) as toml_file:
        instances = toml.loads(toml_file.read())
        
    for key, value in instances.iteritems():        
        if value["controller"] == controller:
            func_name, out_file_name = make_function(key, is_matlab)
            class_name = make_class_name(value["dc_number"])
            value["func_name"] = func_name
            value["class_name"] = class_name
            value["year"] = str(datetime.datetime.now().year)
            if controller == "DC1371":            
                value["dc1371_type"] = make_dc1371_type(value["num_chip_selects"], is_matlab)
            try:
                value["spi_reg"] = format_spi_regs(value["spi_reg"], template, is_matlab)
            except:
                pass #DC718 doesn't take any spi registers
            
            instance = replace_values(template, value, is_matlab)
            
            folder = make_folder(value["part_number"], is_matlab)
            try:
                os.makedirs(folder)
                if not is_matlab:
                    open(folder + "/__init__.py", 'a').close()
            except:
                pass
            with open( folder + "/" + out_file_name, "wt") as out_file:
                out_file.write(instance)

if __name__ == "__main__":
#    generate("dc718_template.txt", "demoboards.toml", 'DC718')
    generate("dc890_template.txt", "demoboards.toml", 'DC890')
#    generate("dc1371_template.txt", "demoboards.toml", 'DC1371')
#    generate("dc718_matlab_template.txt", "demoboards.toml", "DC718", is_matlab=True)
#    generate("dc1371_matlab_template.txt", "demoboards.toml", "DC1371", is_matlab=True)
    generate("dc890_matlab_template.txt", "demoboards.toml", "DC890", is_matlab=True)
