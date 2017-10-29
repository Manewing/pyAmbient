#!/usr/bin/python

import sys
import inspect

def callerName(skip=2):
    """Get a name of a caller in the format module.class.method

       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

       An empty string is returned if skipped levels exceed stack height
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
      return ''
    parentframe = stack[start][0]

    name = []
    module = inspect.getmodule(parentframe)

    # `modname` can be None when frame is executed directly in console
    if module:
        name.append(module.__name__)
    else:
        name.append("console")

    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call
        #   - it will be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)

    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append( codename ) # function or a method

    # Avoid circular refs and frame leaks
    del parentframe, stack

    return ".".join(name)

class Logger(object):

    # different logging modes
    modes = { 0: "DEBUG", 1: "INFO", 2: "WARN", 3: "ERROR" }

    def __init__(self, stream = sys.stderr, level = 0):
        self.stream = stream

        # logging levels:
        #   0 = Debug
        #   1 = Verbose/Info
        #   2 = Warning
        #   3 = Error
        self.level = level


    def setLevel(self, level):
        if level < 0:
            level = 0
        elif level > 3:
            level = 3
        self.level = level

    def __log(self, mode, msg, obj):
        if not self.level <= mode:
            return

        # get name of caller name 'module.function'
        caller_name = callerName(3)
        if obj:
            caller_name = "{}<{}>".format(caller_name, hex(id(obj)))

        # get mode name
        mode_name = Logger.modes[mode]

        self.stream.write("[{}]({}): {}\n".format(mode_name, caller_name, msg))

    def logDebug(self, msg, obj=None):
        self.__log(0, msg, obj)

LOGGER = Logger()
