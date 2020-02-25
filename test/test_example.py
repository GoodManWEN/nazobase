import vapoursynth as vs
from nazobase import *

def test_example():
    # Since vapoursynth environment & reliables automaticly setup goes extremely difficult ,
    # hence this repo has no unit test. 
    assert True

def test_check():
	core = vs.core

	clip1080 = core.std.BlankClip(width = 1920 , height = 1080 , fpsnum=24000 , fpsden=1001)
	clip720 = core.std.BlankClip(width = 1280 , height = 720 , fpsnum=24000 , fpsden=1001)
	r1 = check(clip1080 , clip720)
	assert r1.format.name == clip1080.format.name
	assert r1.width == 1920 and r1.height == 1080
	assert r1.fps_num == 48000 and r1.fps_den == 1001
	assert r1.num_frames == 478

	# YUV420 = ToYUV(clip720 , css='420' ,depth=10)
	# r2 = check(YUV420 , clip1080)
	# assert r2.format.name == 'YUV420P10'
	# assert r2.width == 1280 and r2.height == 720

	# YUV444 = ToYUV(clip1080 , css='420' ,depth=16)
	# r3 = check(YUV444 , clip720)
	# assert r3.format.name == 'YUV420P16'
	# assert r3.width == 1920 and r3.height == 1080
	
	GRAY = core.std.ShufflePlanes(clip1080,0,vs.GRAY)
	r4 = check(GRAY , clip720)
	assert r4.format.name == 'Gray8'

def test_gp():
	core = vs.core

	clip1080 = core.std.BlankClip(width = 1920 , height = 1080 , fpsnum=24000 , fpsden=1001)
	r1 = gp(clip1080)
	
	assert r1.format.name == 'Gray8'

# fmtc needed.
# def test_resize():
# 	core = vs.core

# 	clip720 = core.std.BlankClip(width = 1280 , height = 720 , fpsnum=24000 , fpsden=1001)
# 	clip720 = ToYUV(clip720 , css='444' , depth=16)
# 	r1 = quickresize(clip720, 1920, 1080, 'bicubic', filter_param_a = 1/3, filter_param_b = 1/3)
# 	assert r1.width == 1920 and r1.height == 1080

# 	r2 = quickresize(clip720, 1920, 1080, 'spline16')
# 	assert r2.width == 1920 and r2.height == 1080

# 	r3 = quickresize(clip720, 1920, 1080, 'spline36')
# 	assert r3.width == 1920 and r3.height == 1080

def test_diff():
	core = vs.core

	clip1080 = core.std.BlankClip(width = 1920 , height = 1080 , fpsnum=24000 , fpsden=1001)
	clip720 = core.std.BlankClip(width = 1280 , height = 720 , fpsnum=24000 , fpsden=1001)

	r1 = diff(clip1080 , clip720 ,amp=100)
	assert r1.fps_num == 24000 and r1.fps_den == 1001
	assert r1.format.name == clip1080.format.name
