# Endows a function with arbitrary attributes
#
# Usage:
#
# Instead of calling some function as `output = function(*args, **kwargs)`
# you can wrap the function as
def endow(function, **attributes):

    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    print(attributes)
    for attribute, value in attributes.items():
        setattr(wrapper, attribute, value)
        
        if callable(value):
            value.caller = wrapper
    
    return wrapper

def remember(*args, **kwargs):

    return remember.caller(*args, **kwargs)