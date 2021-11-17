from ctypes import *
from asts import ASTS

class MTEMSG:
    class MSG(Structure):
        _fields_ = [
            ('DataLen', c_int32),
            ('Data', c_char),
        ]

    def __init__(self):
        self._msg = POINTER(MTEMSG.MSG)()
        #self._msg = (c_char * 8)()
        pass

    def pointer(self):
        return byref(self._msg)

    def _toData(self):
        self._data = cast(byref(self._msg[0]), POINTER(c_char * (self._msg.contents.DataLen + 4))).contents
        #self._data = self._msg.contents.Data.contents
        #self._dataLen = int.from_bytes(self._msg[0:4], byteorder='little', signed=False)
        #self._data = cast(self._msg[4:], POINTER(c_char * self._dataLen)).contents
        self._offset = 4

    def _getString(self):
        _len = int.from_bytes(self._data[self._offset:self._offset + 4], byteorder='little', signed=False)
        self._offset += 4
        _str = c_char_p(self._data[self._offset:self._offset + _len]).value.decode('cp1251')
        self._offset += _len
        return _str

    def _getInteger(self):
        _int = int.from_bytes(self._data[self._offset:self._offset + 4], byteorder='little', signed=False)
        self._offset += 4
        return _int

    def _getByte(self):
        _byte = self._data[self._offset:self._offset + 1]
        self._offset += 1
        return _byte

    def _getByteArray(self, _size):
        _byte = self._data[self._offset:self._offset + _size]
        self._offset += _size
        return _byte

    ENUM_KIND = ('ekCheck', 'egGroup', 'ekCombo')

    def _getEnumConst(self):
        if self._version >= 2:
            return {
                'Значение': self._getString(),
                'ДлинноеОписание': self._getString(),
                'КраткоеОписание': self._getString(),
            }
        else:
            return self._getString()

    def _getEnumConsts(self):
        _res = []
        for i in range(self._getInteger()):
            _res.append(self._getEnumConst())
        return _res

    def _getEnumType(self):
        return {
            'Имя': self._getString(),
            'Заголовок': self._getString(),
            'Описание': self._getString() if self._version >= 2 else None,
            'Размер': self._getInteger(),
            'Тип': MTEMSG.ENUM_KIND[self._getInteger()],
            'Константа': self._getEnumConsts(),
            #'': self._get(),
            #'': self._get(),
        }

    def _getEnumTypes(self):
        _res = []
        for i in range(self._getInteger()):
            _res.append(self._getEnumType())
        return _res

    FIELD_FLAGS = {
        0x01: 'ffKey',
        0x02: 'ffSecCode',
        0x04: 'ffNotNull',
        0x08: 'ffVarBlock'
    }
    def _getFieldFlags(self):
        _fl = self._getInteger()
        _res = []
        for k in MTEMSG.FIELD_FLAGS:
            if _fl & k:
                _res.append(MTEMSG.FIELD_FLAGS[k])
        return _res

    FIELD_TYPE = ('ftChar', 'ftInteger', 'ftFixed', 'ftFloat', 'ftDate', 'ftTime', 'ftFloatPoint')
    def _getField(self, isInput):
        return {
            'Имя': self._getString(),
            'Заголовок': self._getString(),
            'Описание': self._getString() if self._version >= 2 else None,
            'Размер': self._getInteger(),
            'Тип': MTEMSG.FIELD_TYPE[self._getInteger()],
            'КолвоДесятичЗнаков': self._getInteger() if self._version >= 2 else None,
            'Атрибуты': self._getFieldFlags(),
            'ПеречислимыйТип': self._getString(),
            'ЗначениеПоУмолчанию': self._getString() if isInput else None,
        }

    def _getFields(self, isInput = True):
        _res = []
        for i in range(self._getInteger()):
            _res.append(self._getField(isInput))
        return _res

    TABLE_FLAGS = {
        0x01: 'tfUpdateable',
        0x02: 'tfClearOnUpdate',
        0x04: 'tfOrderbook'
    }
    def _getTableFlags(self):
        _fl = self._getInteger()
        _res = []
        for k in MTEMSG.TABLE_FLAGS:
            if _fl & k:
                _res.append(MTEMSG.TABLE_FLAGS[k])
        return _res

    def _getTable(self):
        return {
            'Имя': self._getString(),
            'Заголовок': self._getString(),
            'Описание': self._getString() if self._version >= 2 else None,
            'ИндексСистемы': self._getInteger() if self._version >= 2 else None,
            'Атрибуты': self._getTableFlags(),
            'ВходныеПоля': self._getFields(),
            'ВыходныеПоля': self._getFields(isInput=False),
        }

    def _getTables(self):
        _res = []
        for i in range(self._getInteger()):
            _res.append(self._getTable())
        return _res

    def _getTransaction(self):
        return {
            'Имя': self._getString(),
            'Заголовок': self._getString(),
            'Описание': self._getString() if self._version >= 2 else None,
            'ИндексСистемы': self._getInteger() if self._version >= 2 else None,
            'ВходныеПоля': self._getFields(),
        }

    def _getTransactions(self):
        _res = []
        for i in range(self._getInteger()):
            _res.append(self._getTransaction())
        return _res

    def toMTEStructure(self, _res, _vers):
        self._version = _vers
        self._toData()
        if _res == ASTS.MTE_TSMR:
            return c_char_p(self._data).value.decode('cp1251')
        elif _res != ASTS.MTE_OK:
            return None

        MTES = {
            'ИмяИнтерфейса': self._getString(),
            'ЗаголовокИнтерфейса': self._getString(),
            'ОписаниеИнтерфейса': self._getString() if self._version >= 2 else None,
            'НомерMsgSet': self._getString() if self._version >= 4 else None,
            'ПеречислимыеТипы': self._getEnumTypes(),
            'Таблицы': self._getTables(),
            'Транзакции': self._getTransactions(),
        }

        return MTES
