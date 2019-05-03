try:
    from mvsfunc import Depth,ToYUV,ToRGB 
except:
    raise ImportError('mvsfunc is required for this script.')

import vapoursynth as vs
from os import path
from inspect import signature, getframeinfo, currentframe
from functools import wraps, partial
from re import search

######################################################
#
#           nazobase distribution
#           version 0.1.17
#
######################################################

'''
functinos:
    dataloader
    check
    diff
    quickresize
    print
    getplane
    autocheck
'''

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
            # due to filtering by set ,list* could not be used in type hint
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
            Your source path
            Last two character of each node matters,
            cause depth conversion depends on them.

        (int first:)
                    \
        
        (int last:)
            Returns the frames between the arguments first and last


    Usage:
        
        import vapoursynth as vs
        import nazobase as nazo

        core = vs.core

        src8, src10, src16 = nazo.dataloader('video.mp4')
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
def check(clipa:vs.VideoNode, *clipbs:vs.VideoNode, **kwargs) -> vs.VideoNode:

    '''
    Automatically adjust format/bit depth/FPS of clip those in clips to clipa,
    and then return a interleaved clip.
    
    The script will automatically traceback your output node ,and label on top left corner using text.Text()

    You should not use it nested ,since based on string backtracing ,that will cause confuse.

    ###############################################
    Attributes:

        VideoNode clipa:
            target videonode for adjusting.

        *(VideoNode clipbs:)
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

    Wrong use:

        from nazobase import *
        
        ...

        check(check(clipa, clipb), clipc).set_output()

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

    # check if function is called as api
    mode_1_flag = True if ('mode' in kwargs and kwargs['mode'] != 0) else False

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
    if not mode_1_flag:
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
            clipbs[num] = Depth(clipbs[num],target_bit_depth)

        # modifying resolusion
        if clip.width != clipa.width or clip.height != clipa.height:
            clipbs[num] = core.resize.Spline16(clipbs[num],clipa.width,clipa.height)

        # post processing
        clipbs[num] = core.std.AssumeFPS(clipbs[num], clipa)
        if not mode_1_flag:
            clipbs[num] = core.text.Text(clipbs[num], node_stack[num+1])
    
    if mode_1_flag:
        return [clipa] + clipbs

    clipa = clipa.text.Text(node_stack[0])
    output_nodes = [clipa] + clipbs
    
    return core.std.Interleave(output_nodes)



@autocheck
def diff(clipa:vs.VideoNode , clipb:vs.VideoNode , amp:int = 10, planes:(None,0,1,2,list) = None, binarize:bool = False, maskedmerge:bool = False) -> vs.VideoNode:

    '''

    Easy function helps you check out differences between clips.
    Expression : luminance = abs( clipa - clipb ) * amp

    ###############################################
    Attributes:

        VideoNode clipa:
            \

        VideoNode clipb:
            Format insensitive ,
            Clipb will be converted into the vary format of clipa at first.

        (int amp:) 
            Adjust strength of the amplifier.

        (int[] planes:)
            \

        (bool binarize:)
            If true, each pair of pixel who are not exactly the same
            will be highlight labeled. 

        (bool maskedmerge:)
            Showing a merged picture of different pixels like using alpha channel.
            Trun on this if you don't like check(src1,diff(src1,src2)).

    '''

    core = vs.core
    funcName = 'diff'

    # normalization & init
    clipa, clipb = partial(check ,mode = 1)(clipa, clipb)

    if planes == None:
        planes = list(range(clipa.format.num_planes))
    elif isinstance(planes,int):
        planes = [planes]
    if len(planes) == 1:
        clipa = clipa.std.ShufflePlanes(planes,vs.GRAY)
        clipb = clipb.std.ShufflePlanes(planes,vs.GRAY)

    # expr & calculate difference
    expr = f"x y - abs {amp} *"
    res = core.std.Expr([clipa, clipb], [expr])
    res_b = res.std.Binarize(threshold = 1, planes = planes if len(planes) > 1 else [0])
    # create maskmerged clip if required
    if maskedmerge:
        blankclip = core.std.BlankClip(width = clipa.width, height = clipa.height,  format = vs.YUV420P8, length = clipa.num_frames, fpsnum = clipa.fps_num, fpsden = clipa.fps_den ,color = [250,60,115])
        blankclip , clipa = partial(check ,mode = 1)(blankclip, clipa)
        return core.std.MaskedMerge(clipa, blankclip, Depth(res_b.std.Expr('x 2 /'),8),  [0,1,2], True)
    elif binarize:
        return res_b
    
    return res



@autocheck
def quickresize(clip:vs.VideoNode, width:(None,int) = None, height:(None,int) = None, kernel:str = "Spline16" ,**resize_kwargs) -> vs.VideoNode:
    
    '''
    resize avoids resampling lose in YUV/RGB converting ,
    use this if there's no need to change color space.

    Default using BT709 & TVrange for animation processing.

    ###############################################
    Attributes:

        VideoNode clip:
            Target.

        (int width:)
            Width will not change if not specified.

        (int height:)
            Height will not change if not specified.

        (str Kernel:)
            The resize kernel we used is components from vapoursynth standard library. Input as string and it will be converted into function by black magic eval().

            Case insensitive.

        (resize_kwargs:)
            Custom resize attributes if you want.

    Usage:

        from nazobase import *

        src = dataloader('video.mp4')
        # convert with bicubic b/c = 1/3
        res = quickresize(src, 1920, 1080, 'bicubic', filter_param_a = 1/3, filter_param_b = 1/3)

        res.set_output()
    
    '''

    # Using BT709 & fulls/fulld=False by default for animation processing.
    core = vs.core
    funcName = "quickresize"
    kernel_id = "com.vapoursynth.resize"
    matrix = "709"

    # obtain pointer of resizer
    plugins = core.get_plugins()
    functions = plugins[kernel_id]["functions"]
    functions = dict(zip(map(lambda x:x.upper(),functions) ,functions))
    try:
        operator = eval(f"core.{plugins[kernel_id]['namespace']}.{functions[kernel.upper()]}")
    except:
        raise KeyError(f"Didn't find kernel {kernel} in vscore with kernel_id {kernel_id} ,check it again." )
    
    # 
    clip = Depth(clip,16) if clip.format.bits_per_sample < 16 else clip

    # processing
    if clip.format.color_family is vs.YUV:
        clipY = core.std.ShufflePlanes(clip,0,vs.GRAY).fmtc.transfer(transs=matrix,transd="linear",fulls=False,fulld=False)
        clipY = operator(clipY,width = width ,height = height , **resize_kwargs).fmtc.transfer(transs="linear",transd=matrix,fulls=False,fulld=False)
        clipC = operator(clip, width=width,height = height,**resize_kwargs)
        res = core.std.ShufflePlanes([clipY,clipC], [0,1,2], vs.YUV)
    elif clip.format.color_family is vs.GRAY:
        res = operator(clip.fmtc.transfer(transs=matrix,transd="linear",fulls=False,fulld=False), width = width, height = height, ** resize_kwargs).fmtc.transfer(transs="linear",transd=matrix,fulls=False,fulld=False)
    else:
        raise Warning('This function is particularly designed for clips in YUV|GRAY color family.')

    if orn_bitdepth < res.format.bits_per_sample :
        res = Depth(res, orn_bitdepth)

    return res



@autocheck
def print(clip:vs.VideoNode , string = '') -> vs.VideoNode:

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