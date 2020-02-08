from pymediainfo import MediaInfo
from operator import itemgetter

P_GENERAL = {'track_type','count','stream_identifier','video_format_list','codecs_video','file_extension','format','format_info','format_extensions_usually_used','commercial_name','format_version' ,'overall_bit_rate_mode','other_overall_bit_rate_mode','frame_rate','isstreamable','writing_application','writing_library','maximum_overall_bit_rate'}

P_VIDEO = {'track_type','count','stream_identifier','streamorder','track_id','format','format_info','commercial_name','format_profile','internet_media_type','codec_id','width','height','pixel_aspect_ratio','display_aspect_ratio','frame_rate_mode','frame_rate','framerate_num','framerate_den','color_space','chroma_subsampling','bit_depth','writing_library','encoded_library_name','default','color_range','matrix_coefficients','format_settings','sampled_width','sampled_height','standard','scan_type','scan_type__store_method','scan_order','format_identifier'}

P_AUDIO = {'track_type','count','stream_identifier','streamorder','track_id','format','other_format','format_info','commercial_name','internet_media_type','codec_id','bit_rate_mode','channel_s','channel_layout','bit_depth','compression_mode','encoded_library_name','encoded_library_version','encoded_library_date','language','muxing_mode','format_identifier','sampling_rate','format_settings__endianness','other_channel_positions'}

def _convert(info):
    if not isinstance(info , str):
        info = str(info)
    if info.isdigit():
        int_ , float_ = int(info) , float(info)
        return int_ if int_ == float_ else float_
    else:
        return info.encode('utf-8')

def get_info(file):
    media_info = MediaInfo.parse(file)
    DTable = {'General' : [P_GENERAL,0] ,'Video' : [P_VIDEO,0] ,'Audio' : [P_AUDIO,0]}
    opt = dict()
    for track in media_info.tracks:
        dic = track.to_data()
        track_type = dic['track_type']
        sets , bias = DTable.setdefault(track_type,[{}, 1])
        if bias == 1:
            continue
        DTable[track_type][1] = 1
        intersect = list(set(dic.keys()) & sets)
        odict = dict(zip(map(lambda x:f"{track_type}_{x}" , intersect) , map(_convert,itemgetter(*intersect)(dic))))
        opt.update(odict)
    return opt

# a = get_info(r'D:\sorayoriv2\[VCB-Studio] Sora yori mo Tooi Basho [01][Ma10p_1080p][x265_flac].mkv')
# lsta = []
# for i,j in a.items():
#     lsta.append((i,j))
# lsta.sort(key=lambda x:x[0])
# for i in lsta:
#     print(i)