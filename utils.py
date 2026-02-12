import logging
import functools
import os
#for getting logger,logfile and handlers if not exist
def get_configured_logger(lname,filename):
    if not os.path.exists('logs'):
        os.makedirs('logs')


    #logger,formatter,handler ,logging logic
    logger=logging.getLogger(lname)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        formatter=logging.Formatter('%(asctime)s : %(funcName)s : %(levelname)s :	%(message)s')
        #filehandler
        f_handler=logging.FileHandler(filename)
        f_handler.setFormatter(formatter)
        f_handler.setLevel(logging.DEBUG)
        logger.addHandler(f_handler)
        #streamhandler
        s_handler=logging.StreamHandler()
        s_handler.setLevel(logging.ERROR)
        s_handler.setFormatter(formatter)
        logger.addHandler(s_handler)
    return logger
logger=get_configured_logger(__name__,"logs/security.log")

#two logging decorators here
#decorator executed on each func
def log_and_protect(func):
    @functools.wraps(func)#function ka name protected rhega 
    def wrapper(*args,**kwargs):
        logger.info(f"calling function  --{func.__name__}")
        try:
            result= func(*args,**kwargs)
        except Exception as e:
            logger.exception(f"can't run function '{func.__name__}'")
            raise e
        else:

            logger.info(f"{func.__name__} executed successfully")
            return result

    return wrapper
#class decorator that execute log_and_protect decorator on each function of the class it is applied to
def log_all_methods(cls):
    for name,method in cls.__dict__.items():
        if callable(method) and not name.startswith("__"):
            setattr(cls,name,log_and_protect(method))
    return cls