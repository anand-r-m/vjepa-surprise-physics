"""M0r: M1 architecture, untrained weights (released init_model, empty checkpoint)."""
from .m1_vjepa import M1VJEPA


class M0r(M1VJEPA):
    name = "M0r"

    def __init__(self, init_seed=0, **kw):
        super().__init__(ckpt_path=None, random_init_seed=init_seed, **kw)
        self.init_seed = init_seed
