from ctypes import *
from asts import ASTS
from metrics import Metrics

class MTEMSG:
    class MSG(Structure):
        _fields_ = [
            ('DataLen', c_int32),
            ('Data', c_char),
        ]

    def __init__(self):
        self._msg = POINTER(MTEMSG.MSG)()
        self.MTEStructure = None
        self.ErrorStr = None
        self._version = None
        self.MTETables = {}

    def isMTEStructure(self):
        return self.MTEStructure != None

    def pointer(self):
        return byref(self._msg)

    def _toData(self):
        self._dataLen = self._msg.contents.DataLen
        Metrics.info('Read: {0:,d} bytes'.format(self._dataLen))
        Metrics.Var['LastRead'] = self._dataLen
        self._data = cast(byref(self._msg[0]), POINTER(c_char * (self._dataLen + 4))).contents
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

    def _getByteList(self, _size):
        _byte = []
        for i in range(_size):
            _byte.append(self._data[self._offset:self._offset + 1])
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
        }

    def _getEnumTypes(self):
        _res = []
        for i in range(self._getInteger()):
            _res.append(self._getEnumType())
        return _res

    FIELD_FLAGS = {
        0x01: 'ffKey',      # Поле является ключевым. Строки таблицы с совпадающими значениями ключевых полей должны объединяться в одну строку
        0x02: 'ffSecCode',  # Поле содержит код финансового инструмента. Рекомендуется учитывать данный флаг при автоматизации процедуры определения
                            # числа знаков после запятой в числовых полях типа ftFloat
        0x04: 'ffNotNull',  # Поле не может быть пустым
        0x08: 'ffVarBlock'  # Поле входит в группу полей, которые могут повторяться несколько раз
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
        0x01: 'tfUpdateable',       # таблица является обновляемой. Для нее можно вызывать функции MTEAddTable/MTERefresh
        0x02: 'tfClearOnUpdate',    # старое содержимое таблицы должно удаляться при получении каждого обновления с помощью функций MTEAddTable/MTERefresh
        0x04: 'tfOrderbook'         # таблица имеет формат котировок и должна обрабатываться соответсвующим образом (см. Замечания по работе с таблицами)
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

    MSG_MODE_STRUCTURE = 0
    MSG_MODE_TABLE = 1
    def _prepareData(self, _res, mode = MSG_MODE_STRUCTURE):
        if _res in (ASTS.MTE_OK, ASTS.MTE_TSMR) or _res > ASTS.MTE_OK:
            if mode == MTEMSG.MSG_MODE_STRUCTURE:
                self.MTEStructure = None
            self.ErrorStr = None
            self._toData()
            if _res == ASTS.MTE_TSMR:
                self.ErrorStr = c_char_p(self._data[self._offset:]).value.decode('cp1251')

    @Metrics()
    def toMTEStructure(self, _res, _vers):
        self._version = _vers
        self._prepareData(_res)
        if _res == ASTS.MTE_OK:
            self.MTEStructure = {
                'Версия': self._version,
                'ИмяИнтерфейса': self._getString(),
                'ЗаголовокИнтерфейса': self._getString(),
                'ОписаниеИнтерфейса': self._getString() if self._version >= 2 else None,
                'НомерMsgSet': self._getString() if self._version >= 4 else None,
                'ПеречислимыеТипы': self._getEnumTypes(),
                'Таблицы': self._getTables(),
                'Транзакции': self._getTransactions(),
            }

    def _findTableFields(self, _table):
        f = []
        for tbl in self.MTEStructure['Таблицы']:
            if tbl['Имя'] ==  _table:
                for fld in tbl['ВыходныеПоля']:
                    f.append({
                        'name': fld['Имя'],
                        'type': fld['Тип'],
                        'size': fld['Размер'],
                        'dec': fld['КолвоДесятичЗнаков'],
                        'key': True if 'ffKey' in fld['Атрибуты'] else False,
                    })
        return f

    def _getRow(self, _flds):
        _cFld = int.from_bytes(self._getByte(), signed=False, byteorder='little')
        _dataLen = self._getInteger()
        _numberFlds = self._getByteList(_cFld) if _cFld > 0 else list(range(len(_flds)))
        _dataFlds = self._getByteArray(_dataLen)
        _offset = 0
        _row = {}
        for i in _numberFlds:
            if isinstance(i, bytes):
                i = int.from_bytes(i, signed=False, byteorder='little')
            _row[_flds[i]['name']] = _dataFlds[_offset:_offset + _flds[i]['size']].decode('cp1251')
            _offset += _flds[i]['size']

        return _row

    def _getRows(self, _flds):
        _res = []
        for i in range(self._getInteger()):
            _res.append(self._getRow(_flds))
        return _res

    @Metrics()
    def toMTETable(self, _res, _table):
        self._prepareData(_res, mode=MTEMSG.MSG_MODE_TABLE)
        if _res < ASTS.MTE_OK:
            return _res

        self._getTableData(_res, _table)

    @Metrics()
    def toMTETables(self, _res):
        self._prepareData(_res, mode=MTEMSG.MSG_MODE_TABLE)
        if _res < ASTS.MTE_OK:
            return _res

        for i in range(self._getInteger()):
            self._getTableData()

    def _getTableData(self, _HTable=None, _tableName=None):
        _ref = self._getInteger()
        if _HTable is not None:
            _fld = self._findTableFields(_tableName)
            self.MTETables[_HTable] = {
                'TableName': _tableName,
                'HTable': _HTable,
                'fields': _fld,
            }
        else:
            _HTable = _ref
            _fld = self.MTETables[_HTable]['fields']
        self.MTETables[_HTable]['rows'] = self._getRows(_fld)

    def closeMTETable(self, _Htable):
        if _Htable in self.MTETables:
            del self.MTETables[_Htable]

    def TableData(self, _table):
        if isinstance(_table, str):
            _table = self.findTable(_table)
        return self.MTETables[_table]

    def findTable(self, table):
        for t in self.MTETables:
            if self.MTETables[t]['TableName'] == table:
                return t

        return -100