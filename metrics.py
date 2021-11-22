from functools import wraps
from time import time_ns


class Metrics:
    _QUEUE = []
    Var = {}
    VAR_LE = 'LastExecute'
    noPrint = False

    def __init__(self, skepSelf=True, showArgs=True, timeSize='ms', noPrint=False, *args, **kwargs):
        self._skepSelf = skepSelf
        self._showArgs = showArgs
        self._timeSize = timeSize
        self.noPrint = noPrint
        pass

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            _qLen = len(self._QUEUE)
            self.startMetric(func.__name__, *((args[1:] if self._skepSelf else args) if self._showArgs else ()))
            result = func(*args, **kwargs)
            for _ in range(_qLen, len(self._QUEUE)):
                self.stopMetric(timeSize=self._timeSize)
            return result

        return wrapper

    @staticmethod
    def startMetric(_name, *args):
        # arg = ('%s%s' %(_name, ', '.join(map(str, args))), time_ns())
        # print('%s Start: %s %s' % ('>>' * (len(Metrics._QUEUE) + 1), _name, ', '.join(map(str, args))) )
        if Metrics.noPrint == False:
            print('%s Start: %s%s' % ('>>' * (len(Metrics._QUEUE) + 1), _name, str(args)))
        Metrics._QUEUE.append((_name, time_ns()))

    @staticmethod
    def stopMetric(timeSize='ms', *args):
        arg = Metrics._QUEUE.pop()
        te = Metrics._time_execute(timeBegin=arg[1], timeSize=timeSize)
        if Metrics.noPrint == False:
            print('%s Stop: %s. Time: %s. %s' % (
                    '>>' * (len(Metrics._QUEUE) + 1),
                    arg[0],
                    te,
                    '. '.join(args)
                )
            )

    @staticmethod
    def info(*args):
        if Metrics.noPrint == False:
            print('%s Info: %s' % ('==' * (len(Metrics._QUEUE)), ', '.join(map(str, args))))

    @staticmethod
    def _time_execute(timeBegin, timeEnd=None, timeSize='ms'):
        if timeEnd is None:
            timeEnd = time_ns()
        if timeSize == 's':
            t = 1e9
        elif timeSize == 'ms':
            t = 1e6
        elif timeSize == 'mks':
            t = 1e3
        else:
            timeSize = 'ns'
            t = 1

        Metrics.Var[Metrics.VAR_LE] = timeEnd - timeBegin
        return '%.3f %s' % ((timeEnd - timeBegin) / t, timeSize)
