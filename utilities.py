


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

    wrapper.__wrapped_name__ = function.__name__

    for attribute, value in attributes.items():
        setattr(wrapper, attribute, value)
        
        if callable(value):
            value.callback = wrapper
    
    return wrapper

#endregion

#region: utility functions

# these are some functions that can be used as attributes for `endow`

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
#     debug_msg="...",
#     log_file="/path/to/file.log"
# ) 
# ```

import inspect, time, sys, traceback

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
def debug(*args, debug_msg=None, log_file=None, **kwargs):

    filename, line_number = get_caller_info()
    print(
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] calling"
        f" {debug.callback.__wrapped_name__} from file:"
        f" {filename}, line: {line_number}...",
        end=" ",
        file=open(log_file, "a") if log_file is not None else sys.stdout
    )
    ti = time.time()
    try:
        out = debug.callback(*args, **kwargs)
        dt = time.time()-ti
        h, m, s = dt//3600, (dt-dt//3600)//60, dt-(dt-dt//3600)//60
        print(
            f"DONE in {h:.0f}h{m:.0f}m{s:.4f}s"+ \
            int(0 if debug_msg is None else 1)*f"\n  [INFO] {debug_msg}",
            file=open(log_file, "a") if log_file is not None else sys.stdout
        )

        return out
    except Exception as e:
        print(
            f"FAILED, error message:\n",
            file=open(log_file, "a") if log_file is not None else sys.stdout
        )
        traceback.print_exc(
            file=open(log_file, "a") if log_file is not None else sys.stdout
        )

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

def id():
    pass

def remember(*args, **kwargs):

    a = {
        "args": args,
        "kwargs": kwargs,

    }

    output = remember.callback(*args, **kwargs)

    a.update({"output": output})

    id = id(*args, **kwargs)

    return output


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

    fnew = endow(f, debug=debug, remember=remember)
    iterator = range(0, 10**8)
    factor = 2

    # Test to see if I can safely overwrite f with wrapper
    # f = endow(f, debug=debug)
    # print("Testing `debug` attribute (w/ `debug_msg`, `log_file`)")
    # result = f.debug(
    #     iterator,
    #     factor=factor,
    #     debug_msg="This is a test of `debug` functionality.",
    #     log_file="test.log"
    # )
    # print(f"result = {result}\n")
    # return
    # IT WORKS!
    
    print("Testing `f`")
    result = f(iterator, factor=factor)
    print(f"result = {result}\n")

    print("Testing wrapped `f`")
    result = fnew(iterator, factor=factor)
    print(f"result = {result}\n")

    # Testing `debug`
    print("Testing `debug` attribute (no kwargs)")
    result = fnew.debug(iterator, factor=factor)
    print(f"result = {result}\n")

    print("Testing `debug` attribute (w/ `debug_msg`)")
    result = fnew.debug(
        iterator,
        factor=factor,
        debug_msg="This is a test of `debug` functionality."
    )
    print(f"result = {result}\n")

    print("Testing `debug` attribute (w/ `debug_msg`, `log_file`)")
    result = fnew.debug(
        iterator,
        factor=factor,
        debug_msg="This is a test of `debug` functionality.",
        log_file="test.log"
    )
    print(f"result = {result}\n")

    print("Testing `debug` attribute (w/ `debug_msg`) and wrong input")
    result = fnew.debug(
        iterator,
        factor=1.,
        debug_msg="This is a test of `debug` functionality.", #won't get printed
    )
    print(f"result = {result}\n")

    # Testing `remember`

if __name__=="__main__":
    test()

#endregion
