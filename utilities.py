#region: endow
# # FUNCTION WRAPPING UTILITY: ENDOW
#
# Endows a function with arbitrary attributes
#
# Usage:
#
# given a generic function `f(*args, **kwargs)` (even built-in), and an
# arbitrary amount of attributes `attr1`, `attr2`, ..., `attrn` 
# (could be values or functions), `endow` can be called to wrap the function 
# and assign each attribute to the returned wrapper:
#
# ```
# from utilities import endow
# 
# def f(*args, **kwargs):
#     ...
#
# # a function that does something before/after calling f
# def attr1(*args, *more_args, **kwargs, **more_kwargs):
#     ...
#     attr1.callback(*args, **kwargs)
#     ...
#
# # a function that doesn't call f
# def attr2(*args2, **kwargs2):
#     ...
# 
# # generic, non-callable attribute  
# attr3 = "Hello world!"
#
# f_endowed = endow(f, attr1=attr1, attr2=attr2, attr3=attr3)
# 
# # same as f(*args, **kwargs)
# f_endowed(*args, **kwargs)
# # calls attr1
# f_endowed.attr1(*args, *more_args, **kwargs, **more_kwargs)
# # calls attr2
# f_endowed.attr2(*args, *more_args, **kwargs, **more_kwargs)
# # calls attr3
# print(f_endowed.attr3)
# # >>> "Hello world!"
# ```
#
# Typically one would use this functionality to recycle code and modify existing
# code with minimal adjustments while still being readable (just call 
# `f=endow(f, attr1, ...)` and change the desired calls to the function as 
# `f -> f.attr1`)

def endow(function, **attributes):

    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    for attribute, value in attributes.items():
        if type(value) is Bundle:
            instance = value.method(
                wrapper,
                function.__name__,
                *value.args,
                **value.kwargs
            )
            setattr(wrapper, attribute, instance.main)
        elif callable(value):
            instance = value(wrapper, function.__name__)
            setattr(wrapper, attribute, instance.main)
        else:
            setattr(wrapper, attribute, value)
    
    return wrapper

#endregion

class Bundle:

    def __init__(self, method, *args, **kwargs):
        self.method = method
        self.args = args
        self.kwargs = kwargs

class BaseMethod:

    def __init__(self, wrapper, wrapped_name):
        self.callback = wrapper
        self.__wrapped_name__ = wrapped_name

#region: utility functions

# these are some functions that can be used as attributes for `endow`

import inspect, time, sys, traceback, numpy, os

def get_caller_info():
    # Get the current frame (the frame of this function)
    current_frame = inspect.currentframe()
    
    # Get the caller's frame (the frame of the function that called debug)
    caller_frame = current_frame.f_back.f_back
    
    # Get the filename and line number from the caller's frame
    filename = caller_frame.f_code.co_filename
    line_number = caller_frame.f_lineno
    
    # Clean up the frame to avoid reference cycles
    del current_frame
    del caller_frame
    
    return filename, line_number

# # DEBUG
#
# simple debugging utility. Features:
# - specify a string for `debug_msg` to provide a custom message for 
#   a specific invocation of `debug`;
# - specify a file name for `log_file` to store messages in an external
#   file instead of piping to stdout.
# 
# Usage:
# 
# ```
# f = endow(f, debug=debug)
# output = f.debug(
#     *args,
#     **kwargs,
#     debug_msg="..."
# ) 
# ```

class debug(BaseMethod):

    def __init__(self, wrapper, wrapped_name, log_file=None, no_arrays=False):
        super().__init__(wrapper, wrapped_name)
        self.log_file = log_file
        self.no_arrays = no_arrays
        self.reset_when_lines = 10000

    def main(self, *args, debug_msg=None, **kwargs):

        if self.log_file is not None:
            self.reset_maybe()

        filename, line_number = get_caller_info()
        
        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] calling"
            f" {self.__wrapped_name__} from file:"
            f" {filename}, line: {line_number}...",
            file=open(self.log_file, "a") if self.log_file is not None else sys.stdout
        )
        ti = time.time()
        
        if self.no_arrays:
            if numpy.__version__[0]=="1":
                numpy.set_string_function(lambda x: "array",  repr=True)
                numpy.set_string_function(lambda x: "array",  repr=False)
            elif numpy.__version__[:3]=="2.0":
                # arrays cannot be completely redacted, try to shorten them as much as possible
                numpy.set_printoptions(
                    threshold=3,
                    edgeitems=1,
                    formatter={"all": lambda x: ""}
                )
            else:
                numpy.set_printoptions(override_repr=lambda x: "array")
        
        try:
            out = self.callback(*args, **kwargs)
            dt = time.time()-ti
            h, m, s = dt//3600, (dt-dt//3600)//60, dt-(dt-dt//3600)//60
            print(
                f"  DONE in {h:.0f}h{m:.0f}m{s:.4f}s" + \
                f"\n  [INPUT] {args} {kwargs}" + \
                f"\n  [OUTPUT] {out}" + \
                int(0 if debug_msg is None else 1)*f"\n  [INFO] {debug_msg}",
                file=open(self.log_file, "a") if self.log_file is not None else sys.stdout
            )

            return out
        except Exception as e:
            print(
                f"FAILED, error message:\n",
                file=open(self.log_file, "a") if self.log_file is not None else sys.stdout
            )
            traceback.print_exc(
                file=open(self.log_file, "a") if self.log_file is not None else sys.stdout
            )

        if self.no_arrays:
            if numpy.__version__[0]=="1":
                numpy.set_string_function(None)
            elif numpy.__version__[:3]=="2.0":
                numpy.set_printoptions(
                    edgeitems=3,
                    infstr='inf',
                    linewidth=75,
                    nanstr='nan',
                    precision=8,
                    suppress=False,
                    threshold=1000,
                    formatter=None
                )
            else:
                numpy.set_printoptions()
  
    def reset_maybe(self):
        
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                lines = 0
                for _ in f:
                    lines += 1
                
            if lines>=self.reset_when_lines:
                os.remove(self.log_file)


# # REMEMBER
#
# simple chaching utility. Features:
#
# 
# Usage:
# 
# ```
# 
# ```

import pickle, hashlib

class remember(BaseMethod):

    def __init__(self, wrapper, wrapped_name, cachedir="./", warn=True):
        super().__init__(wrapper, wrapped_name)
        
        self.path = cachedir.rstrip("/")
        self.warn = warn

    def main(self, *args, cache_id=None, skip=False, **kwargs):

        if skip:
            if self.warn:
                print(f"Warning: You specified you want to skip this function: `{self.__wrapped_name__}`, this might generate errors! Make sure the output of this function doesn't affect other functions in your code.")
            
            return
        
        # if skip is kept to False, caches are generated or loaded
        if cache_id is None:
            args_id = self.get_cache_id(*args, **kwargs)
            
            # get id of wrapped function
            wrapped_id = self.get_cache_id(self.__wrapped_name__)

            # get id of path of filename from which function is called
            filename_id = self.get_cache_id(os.path.abspath(get_caller_info()[0]))

            cache_id = filename_id+wrapped_id+args_id
        
        # check if cache file exists
        cache_path = f"{self.path}/{cache_id}"
        if os.path.exists(cache_path):
            out = pickle.load(open(cache_path, "rb"))

            if self.warn:
                print(f"Warning: Cache was found for `{self.__wrapped_name__}` and given arguments, return type will be {type(out)}.")
            
            return out
        else:
            if self.warn:
                print(f"Warning: Cache was not found for `{self.__wrapped_name__}` and given arguments, the function will run normally and the output will be cached at {cache_path}.")
            
            out = self.callback(*args, **kwargs)
            pickle.dump(out, open(cache_path, "wb"))

            return out
            
    def to_bytes(self, obj):

        def subsample_bytes(arr):
            
            rng = numpy.random.RandomState(893)
            inds = rng.randint(low=0, high=arr.size, size=1000)
            b = arr.flat[inds]
            b.flags.writeable = False
            
            return b.data.tobytes()
    
        if isinstance(obj, (str, int, float, bool, bytes)):
            return str(obj).encode('utf-8')
        elif isinstance(obj, (list, tuple)):
            return b'['+b','.join(map(self.to_bytes, obj))+b']'
        elif isinstance(obj, dict):
            return b'{'+b','.join(
                self.to_bytes(k) + b':'+self.to_bytes(v) for k, v in sorted(obj.items())
            )+b'}'
        elif isinstance(obj, set):
            return b'{'+b','.join(sorted(map(self.to_bytes, obj)))+b'}'
        elif isinstance(obj, numpy.ndarray):
            return subsample_bytes(obj)
        else:
            # Fallback: Use pickle with protocol=4 (deterministic in Python 3.8+)
            import pickle
            return pickle.dumps(obj, protocol=4)

    def get_cache_id(self, *args, hash_algo='sha1', length=6, **kwargs):
        
        hasher = hashlib.new(hash_algo)
        
        hasher.update(self.to_bytes(args))
        hasher.update(self.to_bytes(kwargs))

        full_hash = hasher.hexdigest()
        
        return full_hash[:length] if length else full_hash


#endregion

#region: tests

def test():

    def f(iterator, factor=1):

        sum = 0
        for i in iterator:
            sum += i

        if type(factor) is int:
            sum *= factor 
        else:
            raise AttributeError("cannot use non-integer factor") 

        return sum

    f = endow(
        f,
        debug=Bundle(
            debug,
            log_file=None, #"/path/to/debug.log",
            no_arrays=True # disable printing of arrays
        ),
        remember=remember
    )
    # can also pass it without `Bundle` to use `debug` default arguments
    # f = endow(
    #     f,
    #     debug=debug
    # )
    iterator = range(0, 10**8)
    factor = 2
    
    print("Testing `f`")
    result = f(iterator, factor=factor)
    print(f"result = {result}\n")

    # Testing `debug`
    print("Testing `debug` attribute (no `debug_msg`)")
    result = f.debug(iterator, factor=factor)
    print(f"result = {result}\n")

    print("Testing `debug` attribute (w/ `debug_msg`)")
    result = f.debug(
        iterator,
        factor=factor,
        debug_msg="This is a test of `debug` functionality."
    )
    print(f"result = {result}\n")

    # Testing `remember`
    print("Testing `remember` attribute")
    result = f.remember(
        iterator,
        factor
    )
    print(f"result = {result}\n")

    # retry, it should remember the previous command and there should be a cache file in the working directory
    print("Testing `remember` attribute again (should be faster due to cache loading)")
    result = f.remember(
        iterator,
        factor
    )
    print(f"result = {result}\n")

if __name__=="__main__":
    test()

#endregion
