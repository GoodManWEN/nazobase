try:
    from mvsfunc import Depth,ToYUV,ToRGB 
except:
    raise ImportError('mvsfunc is required for this script.')

import vapoursynth as vs
from os import path
from inspect import signature,getframeinfo,currentframe
from functools import wraps
from re import search
import nazobase as nazo

######################################################
#
#           nazobase distribution
#           version 0.1.15
#
######################################################

def autocheck(func):
    '''

    Datatype auto check ,supports types and values.
    Checkout PEP484 for more information.

    '''
    trace = signature(func)
    reference = func.__annotations__

    def not_instance(value ,target ,name ,reponame):
        if not isinstance(target[name],(tuple,dict)):
            values , types_ = (), target[name]
        else:
            values = tuple(filter(lambda x:False if isinstance(x,type) else True ,target[name] ))
            types_ = tuple( set(target[name]) - set(values) )
        if value in values or isinstance(value, types_):
            return ;
        raise TypeError(f'Argument "{reponame}" must be {target[name]}')

    @wraps(func)
    def wrapper(*args, **kwargs):
        '''

        Simple is better than complex ,
        Complex is better than complicated.

        '''
        for name,value in trace.bind(*args, **kwargs).arguments.items():
            if name in reference:
                if isinstance(value ,tuple):
                    for value_value in value:
                        not_instance(value_value, reference, name, name)
                elif isinstance(value ,dict):
                    for name_name, value_value in value.items():
                        not_instance(value_value, reference, name, name_name)
                else:
                    not_instance(value, reference, name, name)      
        ret = func(*args, **kwargs)
        if 'return' not in reference or isinstance(ret,reference['return']):
            return ret
        raise TypeError(f'Return type of {func.__name__} must be {reference["return"]}')
    return wrapper



# @autocheck
# decorator affacts inspect debuging process should not be used
def dataloader(source:str, first:(None,int) = None, last:(None,int) = None) -> vs.VideoNode:

    '''
    
    Script helps loads data conveniently.

    Auto checks if your input is a video or image.
    *(support type jpg/png/bmp ,ignore case)

    Auto loads the depth you want ,
    support one or more request.

    ###############################################
    Attributes:

        string source:
            your source path

        (int first:)
                    \
        
        (int last:)
            returns the frames between the arguments first and last


    Usage:
        
        import vapoursynth as vs
        import nazobase as nazo

        core = vs.core

        src8,src10,src16 = nazo.dataloader('video.mp4')
        src16.set_output()

        ↑ Thus you'll get three clips with specific depth respectively
        based on string check.

    Have fun.

    '''

    # initialization
    if not isinstance(source, str):
        raise TypeError("Please input a string")

    if not isinstance(first, int) and first != None:
        raise TypeError("Input type error ,attribute first must be a integer")

    if not isinstance(last, int) and last != None:
        raise TypeError("Input type error ,attribute last must be a integer")

    core = vs.core
    funcName = 'dataloader'

    # for the depths which you wanted to catch 
    target_depth = ['8','10','16']

    # checking if input is a image or video
    if path.splitext(source)[1].lower() in ['png','jpg','bmp']:
        clip = core.imwri.Read(source, alpha=False)
    else:
        clip = core.lsmas.LWLibavSource(source,threads=1)
        clip = clip if first == last == None else clip.std.Trim(first,last)

    # trace back trigger command
    request_node_lst = list(map(lambda x:x.strip(),getframeinfo(currentframe().f_back)[3][0].split('=')[0].split(',')))

    # driven table
    return_depth_lst = dict(zip(target_depth,list(map(lambda y:lambda x:Depth(x,int(y)),target_depth))))
    return_depth_lst.update({'0':lambda x:x})

    def selector(_ln):
        try: _ln_ln = search('[\d]+',_ln).group()
        except: _ln_ln = '0'
        return _ln_ln if _ln_ln in target_depth else '0'

    #iterator to return 
    def ret():
        for node in request_node_lst:
            yield return_depth_lst[selector(node[-2:])](clip)

    return ret() if len(request_node_lst) != 1 else next(ret())



# @autocheck
# decorator affacts inspect debuging process should not be used
def check(clipa:vs.VideoNode, *clipbs:vs.VideoNode) -> vs.VideoNode:

    '''
    Automatically adjust format/bit depth/FPS of clip those in clips to clipa,
    and then return a interleaved clip.
    
    The script will automatically traceback your output node ,and label on top left corner using text.Text()

    You should not use it nested ,since based on string backtracing ,that will cause confuse.

    ###############################################
    Attributes:

        VideoNode clipa:
            target videonode for adjusting.

        *(VideoNode clipbs):
            one or more videonode to adjust.
            of course you can also leave it empty.
    
    Usage:

        # a simple demo for checking the relationships between
        # the Cb plane and edge of Luma Plane

        import vapourysynth as vs
        import nazobase as nazo

        core = vs.core

        src10 = nazo.dataloader('video.mp4')

        nazo.check(nazo.getplane(src10,1) , core.tcanny.Tcanny(src10) ).set_output()

    '''

    # initialization
    for clip_ in (clipa,*clipbs):
        if not isinstance(clip_ , vs.VideoNode):
            raise TypeError('Input attributes should all be type of vs.VideoNode')

    core = vs.core
    funcName = 'check'

    clipbs = list(clipbs)
    target_color_family = clipa.format.color_family
    target_bit_depth = clipa.format.bits_per_sample

    # backtracking node list
    def _pop_stack():
        tmp_lst = []
        while True:
            poped = node_stack.pop()
            if poped == "(": break
            tmp_lst.append(poped)
        tmp_lst.reverse()
        if node_stack == []: node_stack.extend(tmp_lst)
        else:node_stack[-1] += f"({', '.join(tmp_lst)})"

    char_opts = {   '(':lambda :node_stack.extend(['(','']) ,
                    ',':lambda :node_stack.append('') ,
                    ' ':lambda :None,
                    ')':_pop_stack      }

    try:
        node_stack = list()
        activate_string = getframeinfo(currentframe().f_back)[3][0]
        activate_string = search('check[\s]*\(.+\)(\.set_output\(\))*',activate_string).group().replace(".set_output()","")
        activate_string = activate_string[activate_string.index('('):len(activate_string)-activate_string[::-1].index(')')]   
    except:
        node_stack = [str(clipa)]
    else:
        for char in activate_string:
            try: char_opts[char]()
            except: node_stack[-1] += char
   
    # options table
    def operate_YUV(clip):
        try:
            return ToYUV(clip,css=search('(420|422|444)',clipa.format.name).group(),full=False,depth=clip.format.bits_per_sample)
        except:
            raise TypeError('Only YUV420/422/444 is supported')

    options = { vs.YUV:operate_YUV,
                vs.RGB:lambda clip: ToRGB(clip,full=False,depth=clip.format.bits_per_sample),
                vs.GRAY:lambda clip: clip.std.ShufflePlanes(0,vs.GRAY)  }

    # operating
    for num,clip in enumerate(clipbs):
        
        tmp_color_family = clip.format.color_family
        if target_color_family not in options or tmp_color_family not in options:
            raise TypeError('This script can only handle format with YUV/RGB/GRAY')
        
        # modifying color family
        if  tmp_color_family != target_color_family:
            clipbs[num] = options[target_color_family](clip)

        # modifying bit depth
        if clipbs[num].format.bits_per_sample != target_bit_depth:
            clipbs[num] = Depth(clipbs[num],clipbs[num].format.bits_per_sample)

        # modifying resolusion
        if clip.width != clipa.width or clip.height != clipa.height:
            clipbs[num] = core.resize.Spline16(clipbs[num],clipa.width,clipa.height)

        # post processing
        clipbs[num] = core.std.AssumeFPS(clipbs[num], clipa)
        clipbs[num] = core.text.Text(clipbs[num], node_stack[num+1])
    
    clipa = clipa.text.Text(node_stack[0])
    output_nodes = [clipa] + clipbs
    
    return core.std.Interleave(output_nodes)



@autocheck
def print(clip:vs.VideoNode , string:str = '') -> vs.VideoNode:

    '''
    used to show variables directly.
    '''

    core = vs.core
    funcName = 'print'

    if not isinstance(string,str):
        string = repr(string)

    return core.text.Text(clip,string)




@autocheck
def getplane(clip:vs.VideoNode , plane:int = 0) -> vs.VideoNode:

    '''
    fast std.ShufflePlanes()
    '''

    core = vs.core
    funcName = 'getplane'

    return core.std.ShufflePlanes(clip,plane,vs.GRAY)



@autocheck
def diff(clipa:vs.VideoNode , clipb:vs.VideoNode , amp:int = 8, planes:(None,int,list) = None) -> vs.VideoNode:
    # under construction
    return clipa
