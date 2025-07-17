# -----------------
# BACKGROUNDS
# -----------------


def background_one(parent, noiseTOP):
    noise = parent.create(noiseTOP, 'bg1')
    noise.viewer = True
    noise.par.period = 1.74
    noise.par.harmon = 5
    noise.par.spread = 0.8
    noise.par.gain = 1.34
    noise.par.exp = 2.72
    noise.par.mono = 0
    noise.par.tz.expr = "me.time.frame/100"
    noise.par.resolutionw = parent.par.w
    noise.par.resolutionh = parent.par.h
    noise.nodeX = -200
    return noise
