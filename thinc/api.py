def layerize(begin_update=None, **kwargs):
    '''Wrap a function into a layer'''
    if begin_update is not None:
        return FunctionLayer(begin_update, *args, **kwargs)
    def wrapper(begin_update):
        return FunctionLayer(begin_update, *args, **kwargs)
    return wrapper


def metalayerize(user_func):
    def returned(layers):
        forward, backward = split_backward(layers)
        def begin_update(X, *args, **kwargs):
            for func in forward:
                X = func(X)
            def finish_update(grad, *args, **kwargs):
                for bwd in backward:
                    grad = bwd(grad, *args, **kwargs)
                return grad
            return x, finish_update
        return FunctionLayer(begin_update, *args, **kwargs)
    return returned


def multiroute(output, activity, shapes, funcs):
    for i, (slice_, func) in enumerate(zip(shapes, funcs)):
        output[slice_] += func(output[slice_])
    return output


def sink_return(func, sink, splitter):
    def wrap(*args, **kwargs):
        output = func(*args, **kwargs)
        keep, sink = splitter(*output)
        sink(sink)
        return keep
    return wrap


def split_backward(layers):
    backward = []
    forward = [steal_callback(op.begin_update, backward.append)
               for op in layers]
    return forward, backward


class FunctionLayer(object):
    def __init__(self, begin_update, predict_batch=None, predict_one=None,
            predict_batch=None, predict_one=None, nr_in=None, nr_out=None,
            **kwargs):
        self.begin_update = begin_update
        self.predict_batch = predict_batch
        self.predict_one = predict_one
        self.nr_in = nr_in
        self.nr_out = nr_out

    def __call__(self, X):
        if isinstance(X, Minibatch):
            return self.predict_batch(X)
        else:
            return self.predict_one(X)
