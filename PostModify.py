from bs4 import BeautifulSoup
from jinja2 import Template
from requests import get
from operator import itemgetter
from shutil import copyfile
from os import remove
from inspect import isfunction ,isclass
import logging ,re 

DEBUG = True

url = 'https://github.com/GoodManWEN/nazobase'
release = f'{url}/releases/latest'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8"
}

def fix(file ,replacement):
    with open(file,'r',encoding='utf-8') as f:
        template = Template(f.read())
        out = template.render(**replacement)
    with open(file,'w',encoding='utf-8') as f:
        f.write(out)

# Since CI/CD environment can not support vs install 
# we need to findout other means where we don't need to import package.
if DEBUG:
    copyfile('./nazobase/base.py','testbase.py')

with open('testbase.py','r',encoding='utf-8') as f:
    cont = f.readlines() 
cont.insert(0,'panaceafunc = lambda *args,**kwargs:None\n')

out_cont = []
for i , line in enumerate(cont):
    if line[:4] != ' '*4 and (re.search('from(.*?)import(.*?)',line) or re.search('import(.*?)as(.*?)',line)):
        if '.' in line:
            if ' as ' in line:
                libs = line[line.index(' as ')+4:].split(',')
            else:
                libs = line[line.index('import ')+7:].split(',')
            libs = list(map(lambda x:x.strip(), libs))
            out_cont.append(f"{','.join(libs)} = {','.join(['panaceafunc'] * len(libs))}\n")
        elif 'vapoursynth' in line:
            out_cont.append('class new:pass\n')
            out_cont.append('vs=new()\n')
            out_cont.append('vs.VideoNode=panaceafunc\n')
        else:
            out_cont.append(line)
    else:
        out_cont.append(line)

with open('testbase.py','w',encoding='utf-8') as f:
    f.writelines(out_cont)

import testbase
from testbase import *

with open('testbase.py','r',encoding='utf-8') as f:
    cont = f.read()
locals_ = locals()
var_cont = dir(testbase)
func_name_list = list()
for var in var_cont:
    if var[0] != '_' and isfunction(locals_[var]):
        reslt = re.search(f'\n(\s*)def {var}',cont)
        if reslt:
            func_name_list.append(var)

func_list = itemgetter(*func_name_list)(locals_)
logging.info(f"Find functions : {','.join(func_name_list)}")
func_name = '\n#   '.join(func_name_list)
doc_whole = "\n'''"
for i , func in enumerate(func_list):
    doc_whole += f"\n# Function name : [[{func_name_list[i]}]]\n######################################################\n"
    doc_whole += '\n'.join(map(lambda x:x[4:] if x[8:16] == '#'*8 else x[2:] , func.__doc__.split('\n')))
    doc_whole += "\n######################################################"
doc_whole += "\n'''"

func_name_list = list()
for var in var_cont:
    reslt = re.search(f'\n(\s*)def {var}',cont)

html = BeautifulSoup(get(url , headers).text ,'lxml')
descript = html.find('meta' ,{'name':'description'}).get('content')
html = BeautifulSoup(get(release , headers).text ,'lxml')
version = html.find('div',{'class':'release-header'}).find('a').text
logging.info(f'Version number : {version} fetched.')
if not DEBUG:
    fix('setup.py' , {'short_dscp':descript ,"version_release":version})
    fix('./nazobase/__init__.py' , {"funcs":func_name,"func_dscp":doc_whole ,"version_release":version})
else:
    print(f"descript = {descript}")
    print(f"version = {version}")
    print(f"func_name = {func_name}")
    print(f"doc_whole = {doc_whole}")
    remove('testbase.py')