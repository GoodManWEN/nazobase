class options:

    def __init__(self , **kwargs):
        self.nr = { # Degrain
            'd': 1, 'a': 1, 's': 3,
            'hy': 1.9, 'hc': 1.15, 'hy2': 3.6, 'hc2': 1.6,
            'device_type': 'GPU','device_id': 0 }
        self.f3kdb = { #f3kdb USM
            'f3str': 0.36 }
        self.gaussain = { # Gaussain USM
            'bsigma': 1.32, 'dgmode': 1, 'pdgp': 45 } 
        self.aamod = { #AA
            'aakernel': 1, 'cycle': 1, 'eesigma': 0.5, 'elsigma': 1.5,
            'Text_Protect': False }
        self.dbmod = { #modDB
            'left': 64, 'right': 22, 'anc_x': 0.38, 'anc_y': 96, 'dbsty': 48, 'dbstc': 32,
            'range1': 12, 'range2': 16, 'range3': 40,'thr': 0.6, 'thc': 0.4, 'est': 1.6,
            'dbamp': 1.0, 'chroma': False, 'tp': False, 'Time_domain_p': False }
        self.dering = { #Dering
            'rbias': 1.1 ,'drgamma': 3, 'drrx': 1.5, 'dramp': 200,
            'limited_dering': True }
        self.linedarken = { #LineDarken
            'Line_Darken': True,
            'ldamp': 1, 'limit': 1, 'thrs': 512 }
        self.warp = { # LineWrap
            'Warpline': False,
            'wthresh': 28, 'wblur': 2, 'wdepth': 12, 'wplane': 0 }
        self.post_wf2x = { # Post-wf2x
            'Limited_wf2x': 0, # 2:limit mode 1:normal mode 0:off
            # currently this function is disabled
            'matr': [0,1,0,1,1,0,1,0],
            'matr0': [1,1,1,1,1,1,1,1],
            'matrmode': 1, # 1:normal 0:slight
            'wfnoise': 0, 'wfscale': 1, 'wfslice': 1, 'wfmode': 1, 'wfshift': 0.25 }
        self.masks = {
            'mmsigma': 1.5, 'mmh': 389.60 ,'mml': 48.97,
            'glmgama': 1.08 , 'glmest1': 299.52 , 'glmest2': 120.32,
            'cmplimitY': 265, 'cmplimitC': 245, 
            'cmlowlimit1': 312, 'cmlowlimit2': 341, 'cmlowlimit3': 129,
            'cmdelta': 2, 'cmradius': 1.8, 'cmblursigma': 1.5 }
        self.misc = { # Misc
            'VSMaxPlaneNum': 3, 
            'debugmode': 1 }

        self.update(**kwargs)

    def update(self, **kwargs):
        for key , prodict in self.__dict__.items():
            for ikey , ival in kwargs.items():
                if ikey in prodict and ikey[0] != "_": # Avoid hidden attribute
                    self.__dict__[key][ikey] = ival

    def params(self):
        opt_str = "Parameters:\n"
        for key , prodict in self.__dict__.items():
            opt_str += f"# {key} ralated:\n\t"
            count , end , opt_tmp = 0 ,len(prodict) ,""
            for ikey , ival in prodict.items():
                count += 1
                opt_tmp += f"[{ikey}]: {ival}{', ' if count != end else ''}"
                if len(opt_tmp) >= 33:
                    bias = '\t' if count != end else ''
                    opt_str += opt_tmp + f"\n{bias}"
                    opt_tmp = ''
            else:
                if opt_tmp != "":
                    opt_str += opt_tmp + '\n' 
                if opt_str[-1] != '\n':
                    opt_str += '\n'
        return opt_str

                    