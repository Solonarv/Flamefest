# Released under Unlicense.
from inspect import getattr_static
import functools

class monkeypatch:
    """ Decorator for all your evil monkeypatching needs.

    Functions as a class decorator:

    @monkeypatch(Foo)
    class FooPatch:
        def bar():
            print("patched!")
    
    will set Foo.bar to the definition of FooPatch.bar.

    @monkeypatch(Foo, 'bar')
    def bar():
        print("patched!")
    
    will do the same, and allows to specify which attribute should be replaced.
    """
    unpatchable_attrs = frozenset([
        '__dict__',
        '__weakref__',
        '__doc__',
        '__module__',
        '__code__'
    ])

    def __init__(self, target, name=None):
        self._target = target
        self._name = name
    
    def __call__(self, thing):
        if self._name:
            if self._name in monkeypatch.unpatchable_attrs:
                raise ValueError(f"Can't monkeypatch attribute {self._name}")
            _do_patch(self._target, self._name, thing)
        if isinstance(thing, type):
            for k, new in thing.__dict__.items():
                name = monkeypatch.cfg.get(new, 'name') or k
                if name not in monkeypatch.unpatchable_attrs:
                    _do_patch(self._target, name, new)
        return thing
    
    class cfg:
        """Allows to configure the behavior of monkeypatch for a specific element.

        inject_old - bool or string, default False. Injects the old member as an argument.
        name - name of the element to replace
        skip - skip this element.
        """
        inject_old = False
        name = None
        skip = False
        def __init__(self, *, inject_old=False, name=None, skip=False):
            self.inject_old = inject_old
            self.name = name
            self.skip = skip

        def __call__(self, func):
            func._monkeypatch_cfg = self
            return func
        
        @classmethod
        def get(cls, thing, key):
            inst = getattr(thing, '_monkeypatch_cfg', cls)
            return getattr(inst, key)

def _do_patch(target, name, new):
    if monkeypatch.cfg.get(new, 'skip'):
        return
    old_argname = monkeypatch.cfg.get(new, 'inject_old')
    if old_argname:
        if old_argname == True:
            old_argname = '_old'
        old = getattr_static(target, name, None)
        new._old_val = old
        @functools.wraps(new)
        def wrapped(*args, **kwargs):
            return new(*args, **{old_argname: new._old_val, **kwargs})
        _new = wrapped
    else:
        _new = new
    setattr(target, name, _new)
    

