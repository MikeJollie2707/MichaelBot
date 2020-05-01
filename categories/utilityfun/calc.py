from math import *
import ast
def calculate(expression):
    safe_list = ['acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 
                 'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 
                 'fmod', 'frexp', 'hypot', 'ldexp', 'log', 'log10', 
                 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 
                 'tan', 'tanh']
    safe_dict = dict([(k, locals().get(k, None)) for k in safe_list])
    answer = "" 
    try:
        answer = eval(expression, {"__builtins__":None}, safe_dict)
        answer = str(answer)
    except ZeroDivisionError as zde:
        answer = "Infinity/Undefined"
    except Exception:
        answer = "Error"
    return answer