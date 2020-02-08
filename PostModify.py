from bs4 import BeautifulSoup
from jinja2 import Template
from requests import get
from operator import itemgetter
import logging ,re


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

with open('testbase.py','r',encoding='utf-8') as f:
    cont = f.readlines() 
cont.insert(0,'panaceafunc = lambda *args,**kwargs:None\n')

for i , line in enumerate(cont):
    if line[:4] != ' '*4 and (re.search('from(.*?)import(.*?)',line) or re.search('import(.*?)as(.*?)',line)):
        if '.' in line:
            if ' as ' in line:
                libs = line[line.index(' as ')+4:].split(',')
            else:
                libs = line[line.index('import ')+7:].split(',')
            libs = list(map(lambda x:x.strip(), libs))
            cont.pop(i)
            cont.insert(i,f"{','.join(libs)} = {','.join(['panaceafunc'] * len(libs))}\n")
        if 'vapoursynth' in line:
            cont.insert(i+1,'vs.VideoNode=panaceafunc\n')
            cont.insert(i+1,'vs=new()\n')
            cont.insert(i+1,'class new:pass\n')
            
with open('testbase.py','w',encoding='utf-8') as f:
    f.writelines(cont)

import testbase
from testbase import *

with open('testbase.py','r',encoding='utf-8') as f:
    cont = f.read()
var_cont = dir(testbase)
func_name_list = list()
for var in var_cont:
    reslt = re.search(f'\n(\s*)def {var}',cont)
    if reslt and var[0] != '_':
        func_name_list.append(var)
func_list = itemgetter(*func_name_list)(locals())
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
fix('setup.py' , {'short_dscp':descript ,"version_release":version})
fix('./nazobase/__init__.py' , {"funcs":func_name,"func_dscp":doc_whole ,"version_release":version})
