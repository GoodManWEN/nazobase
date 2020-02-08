#try:
#    from .mvsfunc1610 import Depth,ToYUV,ToRGB 
#except:
#    raise ImportError('mvsfunc is required for this script.')

import vapoursynth as vs
from .mvsfunc1610 import Depth,ToYUV,ToRGB 
from .MediaInfoVS import get_info
from .nazolib import main as naobu_c
from .options import options
from os import path
from inspect import signature, getframeinfo, currentframe
from functools import wraps, partial
from re import search
dep = Depth

def _autocheck(func):
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



# @_autocheck
# decorator affacts inspect debuging process should not be used
def dataloader(source:str, first:(None,int) = None, last:(None,int) = None, info:bool = False) -> vs.VideoNode:

    '''
    
    Script helps loads data conveniently.

    Auto checks if your input is a video or image.
    *(support type jpg/png/bmp ,ignore case)

    Auto loads the depth you want ,
    support one or more request.

    ######################################################
    Attributes:

        string source:
            Your source path
            Last two character of each node matters,
            cause depth conversion depends on them.

        (int first:)
                    \
        
        (int last:)
            Returns the frames between the arguments first and last

        (bool info:)
            Switch if you want to attach media info of source into frames.


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
        clip = clip if first is None else clip.std.Loop(first)
    else:
        clip = core.lsmas.LWLibavSource(source,threads=1)
        clip = clip if first == last == None else clip.std.Trim(first,last)

    if info:
        clip_info = get_info(source)
        for key, value in clip_info.items():
            if isinstance(value, int):
                clip = clip.std.SetFrameProp(prop = key ,intval = value)
            elif isinstance(value, float):
                clip = clip.std.SetFrameProp(prop = key ,floatval = value)
            else:
                clip = clip.std.SetFrameProp(prop = key ,data = value)
        # python access
        # def set_frame_props(n, f):
        #     fout = f.copy()
        #     for key, value in clip_info.items():
        #         fout.props[key] = value
        #     return fout
        # clip = clip.std.ModifyFrame(clip, set_frame_props)

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



# @_autocheck
# decorator affacts inspect debuging process should not be used
def check(clipa:vs.VideoNode, *clipbs:vs.VideoNode, **kwargs) -> vs.VideoNode:

    '''
    Automatically adjust format/bit depth/FPS of clip those in clips to clipa,
    and then return a interleaved clip.
    
    The script will automatically traceback your output node ,and label on top left corner using text.Text()

    You should not use it nested ,since based on string backtracing ,that will cause confuse.

    ######################################################
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
        
        tmp_format = clip.format
        if target_color_family not in options or tmp_format.color_family not in options:
            raise TypeError('This script can only handle format with YUV/RGB/GRAY')
        
        # modifying color family if different / or different css in YUV 
        if  (tmp_format.color_family != target_color_family) or (target_color_family is vs.YUV and clipa.format.name[:6] != tmp_format.name[:6]):
            clipbs[num] = options[target_color_family](clip)

        # modifying bit depth
        if clipbs[num].format.bits_per_sample != target_bit_depth:
            clipbs[num] = Depth(clipbs[num],target_bit_depth)

        # modifying resolusion
        if clip.width != clipa.width or clip.height != clipa.height:
            clipbs[num] = core.resize.Spline16(clipbs[num],clipa.width,clipa.height)

        # post processing
        if clipa.fps_num != 0 and clipa.fps_den != 0:
            clipbs[num] = core.std.AssumeFPS(clipbs[num], clipa)
        if not mode_1_flag:
            clipbs[num] = core.text.Text(clipbs[num], node_stack[num+1])
    
    if mode_1_flag:
        return [clipa] + clipbs

    clipa = clipa.text.Text(node_stack[0])
    output_nodes = [clipa] + clipbs
    
    return core.std.Interleave(output_nodes)



@_autocheck
def diff(clipa:vs.VideoNode , clipb:vs.VideoNode , amp:int = 10, planes:(None,0,1,2,list) = None, binarize:bool = False, maskedmerge:bool = False):# -> vs.VideoNode:

    '''

    Easy function helps you check out differences between clips.
    Expression : luminance = abs( clipa - clipb ) * amp

    ######################################################
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
            Showing a merged picture of differences between pixels like using alpha channel.
            Trun on this if you don't like "check(src1,diff(src1,src2))".

    '''

    core = vs.core
    funcName = 'diff'

    # normalization & init
    clipa, clipb = partial(check ,mode = 1)(clipa, clipb)

    if planes == None:
        planes = list(range(clipa.format.num_planes))
    elif isinstance(planes,int):
        planes = [planes]

    # shuffle if required
    if len(planes) == 1:
        # Since vsedit calls bif"resize" of vapoursyth to generate RGB clips and output on your screen, it may cause confuse. Matrix for convert is not specified when you cut-out a single plane from RGB format and named its color family as GRAY, thus may cause runtime fail when you preview.
        if clipa.format.color_family is vs.RGB:
            clipa = clipa.std.SetFrameProp(prop="_Matrix", intval = 2)
            clipb = clipb.std.SetFrameProp(prop="_Matrix", intval = 2)
        clipa = clipa.std.ShufflePlanes(planes,vs.GRAY)
        clipb = clipb.std.ShufflePlanes(planes,vs.GRAY)

    # expr & calculate difference
    expr = f"x y - abs {amp} *"
    res = core.std.Expr([clipa, clipb], [expr])
    res_b = res.std.Binarize(threshold = 1, planes = planes if len(planes) > 1 else [0])

    # create maskmerged clip if required
    if maskedmerge:
        iter_ = {x:None for x in list(range(3))}
        clips =[ [f'clipa.std.ShufflePlanes({x}, vs.GRAY)' for x in {2:iter_}.setdefault(y,[0]*3)]
                for y in iter_ ]
        for plane in iter_:
            # Instancing when activate
            iter_[plane] = eval(clips[clipa.format.color_family//int(1e6) - 1][plane]).std.BlankClip(color = list(map( lambda x: x << (clipa.format.bits_per_sample-8), [250,60,115] ))[plane] )
        blankclip = core.std.ShufflePlanes(list(iter_.values()), [0,0,0] ,vs.YUV)

        # convert to rgb if needed
        if clipa.format.color_family is vs.RGB:
            blankclip = ToRGB(blankclip,full=True)
        
        blankclip , clipa = partial(check ,mode = 1)(blankclip, clipa)
        return core.std.MaskedMerge(clipa, blankclip, res_b,  [0,1,2], True)

    elif binarize:
        return res_b
    
    return res



@_autocheck
def quickresize(clip:vs.VideoNode, width:(None,int) = None, height:(None,int) = None, kernel:str = "Spline16" ,**resize_kwargs) -> vs.VideoNode:
    
    '''
    resize avoids resampling lose in YUV/RGB converting ,
    use this if there's no need to change color space.

    Default using BT709 & TVrange for animation processing.

    ######################################################
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
    orn_bitdepth = clip.format.bits_per_sample

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



# @_autocheck
# def print(clip:vs.VideoNode , string = '') -> vs.VideoNode:

#     '''
#     used to show variables directly.
#     '''

#     core = vs.core
#     funcName = 'print'

#     if not isinstance(string,str):
#         string = repr(string)

#     return core.text.Text(clip,string)


@_autocheck
def gp(clip:vs.VideoNode , plane:int = 0) -> vs.VideoNode:

    '''
    fast std.ShufflePlanes()
    '''

    core = vs.core
    funcName = 'gp'

    return core.std.ShufflePlanes(clip,plane,vs.GRAY)


@_autocheck
def nazo3d(clip:vs.VideoNode , nrluma:(float,int) = 1.9 , nrchroma:(float,int) = 1.15 , profile:str = "np" , d:int = 1 , a:int = 2 ,s:int = 3)-> vs.VideoNode:
    '''
    Wrapper of BM3D ,with optional degrain method,
    and final estimate corrections.

    ######################################################
    Attributes:

        VideoNode clip:
            Target.
            RGB24 to RGBS ;
            YUV420 / 422 / 444 P8/P16/P32 ;
            GRAY8 to GRAYS accepted.

        (float nrluma:)
            The strength of denoising, valid range [0, +inf)

        (float nrchroma:)
            The strength of denoising, valid range [1, +inf).
            Processing method of chroma planes will switch between BM3D and NL-meansbe ,which is selected by whether this value is larger than 1.6 .

        (str profile:)
            Preset profiles of BM3D.
            A table below shows the default parameters for each profile.

            "fast" - Fast Profile (default)
            "lc" - Low Complexity Profile
            "np" - Normal Profile
            "high" - High Profile
            "vn" - Very Noisy Profile

        (int d:)
            Set the number of past and future frame that the filter uses for denoising the current frame of KNL-means. d=0 uses 1 frame, while d=1 uses 3 frames and so on. Usually, larger it the better the result of the denoising. Temporal size = (2 * d + 1).
        
        (int a:)
            Set the radius of the search window. a=0 uses 1 pixel, while a=1 uses 9 pixels and so on. Usually, larger it the better the result of the denoising. Spatial size = (2 * a + 1)^2.  

            Tip: total search window size = temporal size * spatial size.

        (int s:)
            Set the radius of the similarity neighbourhood window of KNL-means ,which take effect in processing chroma planes. The impact on performance is low, therefore it depends on the nature of the noise. Similarity neighborhood size = (2 * s + 1)^2.

    Usage:

        # load source
        ... 
        # 
        src16 = ToYUV(src , css = '444' , depth = 16)
        nr16 = nazo3d(src16 , profile = 'np')
        nr16.set_output()
    
    '''

    core = vs.core
    funcName = 'nazo3d'

    # Pre convert videonode into RGBS
    sformat = clip.format
    color_family = sformat.color_family
    bit_depth = sformat.bits_per_sample
    width , height = clip.width , clip.height
    if color_family is not vs.RGB:
        clipS = core.resize.Bicubic(clip, format=vs.RGBS, matrix_in_s="709", filter_param_a_uv=0, filter_param_b_uv=0.5, range_in_s="limited")
    elif bit_depth is not 32:
        clipS = Depth(clip , 32)
    else:
        clipS = clip

    if width > 1280 and height > 720:
        bm_range = 6
    elif width <= 960 and height <= 540:
        bm_range = 4
    else:
        bm_range = 5

    if color_family is vs.RGB or color_family is vs.GRAY:
        opp = core.bm3d.RGB2OPP(clipS)
        flt = core.bm3d.Basic(opp,  matrix=100, sigma=[nrluma, nrchroma, nrchroma], profile=profile, bm_range=bm_range)
        flt = core.bm3d.Final(opp, flt,  matrix=100, sigma=[nrluma, nrchroma, nrchroma], profile=profile, bm_range=bm_range)
        flt = core.bm3d.OPP2RGB(flt)
        if color_family is vs.GRAY:
            flt = core.resize.Bicubic(flt, format=vs.GRAYS, matrix_s="709", filter_param_a_uv=0, filter_param_b_uv=0.5, range_s="limited")
    elif color_family is vs.YUV:
        # luma
        opp_luma = ToYUV(clipS, matrix='OPP')
        flt_luma = core.bm3d.Basic(opp_luma,  matrix=100, sigma=[nrluma, 0, 0], profile=profile, bm_range=bm_range)
        flt_luma = core.bm3d.Final(opp_luma, flt_luma,  matrix=100, sigma=[nrluma, 0, 0], profile=profile, bm_range=bm_range)
        flt_luma = ToRGB(flt_luma, matrix='OPP')
        nry = core.resize.Bicubic(flt_luma, format=vs.GRAYS, matrix_s="709", filter_param_a_uv=0, filter_param_b_uv=0.5, range_s="limited")

        # chroma
        tmp_clip = Depth(clip , 16) if bit_depth != 16 else clip
        if nrchroma < 1.6:
            # use knlm in order to keep texture
            nruv = tmp_clip.knlm.KNLMeansCL( d = d, a = a, s = s, h = nrchroma,wmode=2, device_type='gpu', device_id=0,channels = "UV" )
        else:
            # converting nrchroma scale . 2.0 -> 1.2 && 3.0 -> 1.7 && 3.6 -> 2.0
            nrchroma = round((nrchroma - 1.6) / 2 + 1.0 , 2)
            downrate_w = 1 << sformat.subsampling_w
            downrate_h = 1 << sformat.subsampling_h
            down = core.fmtc.resample(tmp_clip, width // downrate_w, height // downrate_h, sx=-0.5, css='444', planes=[3, 2, 2])
            rgb_chroma = core.resize.Bicubic(down, format=vs.RGBS, matrix_in_s="709", range_in_s="limited")
            opp_chroma = ToYUV(rgb_chroma, matrix='OPP')
            flt_chroma = core.bm3d.Basic(opp_chroma, matrix=100, sigma=[0, nrchroma, nrchroma], profile=profile, bm_range=bm_range - 2)
            flt_chroma = core.bm3d.Final(opp_chroma,flt_chroma, matrix=100, sigma=[0, nrchroma, nrchroma], profile=profile, bm_range=bm_range - 2)
            flt_chroma = ToRGB(flt_chroma, matrix='OPP')
            nruv = core.resize.Bicubic(flt_chroma, format=vs.YUV444P16, matrix_s="709", filter_param_a_uv=0, filter_param_b_uv=0.5, range_s="limited")
        if bit_depth == 32:
            nruv = Depth(nruv , 32)
        else:
            nry = Depth(nry , 16)
        flt = core.std.ShufflePlanes([nry,nruv],[0,1,2],vs.YUV)

    # output
    if flt.format.bits_per_sample != bit_depth:
        flt = Depth(flt, bit_depth)
    return flt

@_autocheck
def wf2x(clip:vs.VideoNode ,noise:int = 0 ,scale:int = 1 ,block_w:int = None ,block_h:int = None ,model:int = 1,slice:int = 1 ,depth:int = 16 ,shift:(int,float) = 0.25 ,shrink:('dpid','normal','dekernel') = 'dekernel')-> vs.VideoNode:

    '''
    Wrapper of waifu2x-caffe ,speed up your procedure
    by slicing stream into interleave frames ,and
    process them multithreadly.
    It's highly recommended to run some memory load test
    before production.

    ######################################################
    Attributes:

        VideoNode clip:
            Target. YUV/RGB/Gray is accepted.

        (int noise:)
            Denoise level from waifu2x-caffe params.

        (int scale:)
            Geometry xN scale ,from waifu2x-caffe params.

        (int block_w:)
            Block width of each individual process.
            The higher block size brings you higher speed ,
            however larger RAM usage combined.

        (int block_h:)
            Same.
            \
        
        (int model:)
            Resize neural network kernel of waifu2x.

        (int slice:)
            Turn waifu2x into n threads running ,
            helps you squeezing all power of you PC.
            Theoretically this option will brings you 
            n times speed along with n times memory 
            use under enough compute power.

        (int depth:)
            Output depth.
        
        (float shift:)
            Chroma shift of resizing.

        (str shrink:)
            Kernel of shrink method while you convert
            back to YUV after drawing.
            options:
                'dekernel' : always brings more Sharpness.
                'dpid' : new gen scaling algorithm.
                'normal' : general processing.
    
    '''

    core = vs.core
    funcName = 'wf2x'

    if clip.format.bits_per_sample != 32:
        clip = Depth(clip , 32)

    formname = clip.format.name
    ornform = 'YUV' if 'YUV' in formname else ('RGB' if 'RGB' in formname else ('Gray' if 'Gray' in formname else None))
    if not ornform:
        raise TypeError('Only YUV/RGB/GRAY format input is accepted.')
    
    # Pro
    if ornform != 'RGB':
        clip = core.resize.Bicubic(clip, clip.width, clip.height, format = vs.RGBS, matrix_in_s = '709',filter_param_a=1/3, filter_param_b=1/3)
    if block_w == None:
        block_w = int(clip.width/2)
    if block_h == None:
        block_h = int(clip.height/2)
    if slice==1:
        wf = clip.caffe.Waifu2x(noise=noise,scale=scale, block_w=block_w, block_h=block_h, model=model, cudnn=True, processor=1, tta=False)
    else:
        o_l = []
        for i in range(slice):
            o_l.append(clip.std.SelectEvery(cycle=slice, offsets=i).caffe.Waifu2x(noise=noise,scale=scale, block_w=block_w, block_h=block_h, model=model, cudnn=True, processor=1, tta=False))
        wf = core.std.Interleave(o_l)

    if ornform is "RGB":
        return Depth(wf , 16)
    else:
        wf = ToYUV(wf,full=False,depth=32,css='444',matrix=1)
        if ornform is 'Gray':
            return Depth(core.std.ShufflePlanes(wf,0,vs.GRAY),16)
        

        h_w = int(clip.width/2)
        h_h = int(clip.height/2)
        if shrink is 'dekernel':
            wf_1 = wf.std.ShufflePlanes([1],vs.GRAY).descale.Debicubic( h_w, h_h,  b=1/3,  c=1/3, src_left=shift, src_top=0.0)
            wf_2 = wf.std.ShufflePlanes([2],vs.GRAY).descale.Debicubic( h_w, h_h,  b=1/3,  c=1/3, src_left=shift, src_top=0.0)
            flt = core.std.ShufflePlanes([wf,wf_1,wf_2], [0,0,0], vs.YUV)
        elif shrink is 'dpid':
            wf_1 = wf.std.ShufflePlanes([1],vs.GRAY).dpid.Dpid(h_w,h_h)
            wf_2 = wf.std.ShufflePlanes([2],vs.GRAY).dpid.Dpid(h_w,h_h)
            flt = core.std.ShufflePlanes([wf,wf_1,wf_2], [0,0,0], vs.YUV)
        else:
            down = wf.fmtc.resample(h_w, h_h, sx=-0.5, css='444', planes=[3, 2, 2])
            flt = core.std.ShufflePlanes([wf,down],[0,1,2],vs.YUV)

    return Depth(flt,16)

class naobu:

    classic = naobu_c
