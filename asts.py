import time
from ctypes import *
import os
import json
import mtemsg
from metrics import Metrics

class ASTS:
    MTE_OK = 0
    MTE_CONFIG = -1
    MTE_SRVUNAVAIL = -2
    MTE_LOGERROR = -3
    MTE_INVALIDCONNECT = -4
    MTE_NOTCONNECTED = -5
    MTE_WRITE = -6
    MTE_READ = -7
    MTE_TSMR = -8
    MTE_NOMEMORY = -9
    MTE_ZLIB = -10
    MTE_PKTINPROGRESS = -11
    MTE_PKTNOTSTARTED = -12
    MTE_FATALERROR = -13
    MTE_INVALIDHANDLE = -14
    MTE_DSROFF = -15
    MTE_ERRUNKNOWN = -16
    MTE_BADPTR = -17
    MTE_WRONGPARAM = -17
    MTE_TRANSREJECTED = -18
    MTE_REJECTION = -18
    MTE_TEUNAVAIL = -19
    MTE_NOTLOGGEDIN = -20
    MTE_WRONGVERSION = -21
    MTE_LOGON = -30
    MTE_TOOSLOWCONNECT = -31
    MTE_CRYPTO_ERROR = -32
    MTE_THREAD_ERROR = -33
    MTE_NOTIMPLEMENTED = -34
    MTE_ABANDONED = -35
    MTE_TRANSPROCESSED = (MTE_OK, MTE_TRANSREJECTED, MTE_TSMR)

    LANGUAGE_ENG = 'English'
    LANGUAGE_RUS = 'Russian'
    LANGUAGE_UKR = 'Ukrainian'

    class ConnectionStats(Structure):
        _fields_ = [
            ('Size', c_int32),  # must be set to sizeof(TConnectionStats) prior to call
            ('Properties', c_uint32),  # ZLIB_COMPRESSED, FLAG_ENCRYPTED, FLAG_SIGNING_ON
            ('SentPackets', c_uint32),  # number of packets sent in the current session
            ('RecvPackets', c_uint32),  # number of packets received in the current session
            ('SentBytes', c_uint32),  # number of bytes sent in the current session
            ('RecvBytes', c_uint32),  # number of bytes received in the current session
            # fields added in version 2
            ('ServerIPAddress', c_uint32),
            ('ReconnectCount', c_uint32),
            ('SentUncompressed', c_uint32),
            ('RecvUncompressed', c_uint32),
            ('ServerName', c_char * 64),
            # fields added in version 3
            ('TsmrPacketSize', c_uint32),
            ('TsmrSent', c_uint32),
            ('TsmrRecv', c_uint32),
        ]

    def _InitServInfo(self):
        self.ServInfo = {
            'Connected_To_Micex': {'value': None, 'type': c_int, 'size': 4},
            'Session_Id': {'value': None, 'type': c_int, 'size': 4},
            'MICEX_Sever_Name': {'value': None, 'type': c_char_p, 'size': 33},
            'Version_Major': {'value': None, 'type': c_int, 'size': 1},
            'Version_Minor': {'value': None, 'type': c_int, 'size': 1},
            'Version_Build': {'value': None, 'type': c_int, 'size': 1},
            'Beta_version': {'value': None, 'type': c_int, 'size': 1},
            'Debug_flag': {'value': None, 'type': c_int, 'size': 1},
            'Test_flag': {'value': None, 'type': c_int, 'size': 1},
            'Start_Time': {'value': None, 'type': c_int, 'size': 4},
            'Stop_Time_Min': {'value': None, 'type': c_int, 'size': 4},
            'Stop_Time_Max': {'value': None, 'type': c_int, 'size': 4},
            'Next_Event': {'value': None, 'type': c_int, 'size': 4},
            'Event_Date': {'value': None, 'type': c_int, 'size': 4},
            'BoardsSelected': {'value': None, 'type': c_char_p, 'size': -1},
            'UserID': {'value': None, 'type': c_char_p, 'size': 13},
            'SystemId': {'value': None, 'type': c_char, 'size': 1},
            'ServerIp': {'value': None, 'type': c_char_p, 'size': -1},
        }

    def debug(self, param):
        if self._DEBUG == True:
            print('--- START DEBUG ---')
            print(param)
            print('=== end debug ===')

    def __init__(self, LIBPATH = None, DEBUG = False):
        self._DEBUG = DEBUG
        if LIBPATH == None:
            LIBPATH = os.path.dirname(os.path.abspath(__file__))
        self._lib = cdll.LoadLibrary(os.path.join(LIBPATH, 'libmtesrl.so'))
        self._ErrorMsg = create_string_buffer(256)
        self.ConnStats = self.ConnectionStats()
        self._mtemsg = mtemsg.MTEMSG()
        self.Structure = None

        #char* MTEErrorMsg(int32_t code);
        self._lib.MTEErrorMsg.argtypes = [c_int32, ]
        self._lib.MTEErrorMsg.restype = c_char_p
        #char* MTEErrorMsgEx(int32_t code, const char *language);
        self._lib.MTEErrorMsgEx.argtypes = [c_int32, c_char_p]
        self._lib.MTEErrorMsgEx.restype = c_char_p

        # int32_t MTEConnect(const char *params, char *error);
        self._lib.MTEConnect.argtypes = [c_char_p, c_char_p]
        self._lib.MTEConnect.restype = c_int32
        #int32_t MTEDisconnect(int32_t conno);
        self._lib.MTEDisconnect.argtypes = [c_int32, ]
        self._lib.MTEDisconnect.restype = c_int32
        #char* MTEGetVersion();
        self._lib.MTEGetVersion.restype = c_char_p
        #int32_t MTEGetServInfo(int32_t conno, char **buffer, int32_t *len);
        self._lib.MTEGetServInfo.argtypes = [c_int32, POINTER(POINTER(c_char)), POINTER(c_int32)]
        self._lib.MTEGetServInfo.restype = c_int32
        #int32_t MTEConnectionStatus(int32_t conno);
        self._lib.MTEConnectionStatus.argtypes = [c_int32, ]
        self._lib.MTEConnectionStatus.restype = c_int32
        #int32_t MTEConnectionStats(int32_t conno, ConnectionStats *stats);
        self._lib.MTEConnectionStats.argtypes = [c_int32, POINTER(self.ConnectionStats)]
        self._lib.MTEConnectionStats.restype = c_int32
        #int32_t MTESelectBoards(int32_t conno, const char *boards, char *result);
        self._lib.MTESelectBoards.argtypes = [c_int32, c_char_p, c_char_p]
        self._lib.MTESelectBoards.restype = c_int32
        #int32_t MTEStructure(int32_t conno, MTEMSG **msg);
        self._lib.MTEStructure.argtypes = [c_int32, POINTER(POINTER(mtemsg.MTEMSG.MSG))]
        self._lib.MTEStructure.restype = c_int32
        #int32_t MTEStructure2(int32_t conno, MTEMSG **msg);
        self._lib.MTEStructure2.argtypes = [c_int32, POINTER(POINTER(mtemsg.MTEMSG.MSG))]
        self._lib.MTEStructure2.restype = c_int32
        #int32_t __callspec MTEStructureEx(int32_t conno, int32_t version, MTEMSG **msg);
        self._lib.MTEStructureEx.argtypes = [c_int32, c_int32, POINTER(POINTER(mtemsg.MTEMSG.MSG))]
        self._lib.MTEStructureEx.restype = c_int32
        #int32_t MTEOpenTable(int32_t conno, const char *name, const char *params, int32_t complete, MTEMSG **msg);
        self._lib.MTEOpenTable.argtypes = [c_int32, c_char_p, c_char_p, c_int32, POINTER(POINTER(mtemsg.MTEMSG.MSG))]
        self._lib.MTEOpenTable.restype = c_int32
        #int32_t MTEAddTable(int32_t conno, int32_t tabno, int32_t ref);
        self._lib.MTEAddTable.argtypes = [c_int32, c_int32, c_int32]
        self._lib.MTEAddTable.restype = c_int32
        #int32_t MTERefresh(int32_t conno, MTEMSG **msg);
        self._lib.MTERefresh.argtypes = [c_int32, POINTER(POINTER(mtemsg.MTEMSG.MSG))]
        self._lib.MTERefresh.restype = c_int32
        #int32_t MTECloseTable(int32_t conno, int32_t tabno);
        self._lib.MTECloseTable.argtypes = [c_int32, c_int32]
        self._lib.MTECloseTable.restype = c_int32
        #int32_t MTEFreeBuffer(int32_t conno);
        self._lib.MTEFreeBuffer.argtypes = [c_int32, ]
        self._lib.MTEFreeBuffer.restype = c_int32


    def ErrorMsg(self):
        return self._ErrorMsg.value.decode('cp1251')

    def MSGError(self):
        return self._mtemsg.ErrorStr if self._mtemsg.ErrorStr != None else ''

    #char* MTEGetVersion();
    def MTEGetVersion(self):
        return self._lib.MTEGetVersion().decode('utf-8')

    #char* MTEErrorMsg(int32_t code);
    def MTEErrorMsg(self, code):
        return self._lib.MTEErrorMsg(code).decode('cp1251')

    #char* MTEErrorMsgEx(int32_t code, const char *language);
    def MTEErrorMsgEx(self, code, lang=LANGUAGE_ENG):
        return self._lib.MTEErrorMsgEx(code, lang.encode('utf-8')).decode('cp1251')

    #int32_t MTEConnect(const char *params, char *error);
    @Metrics()
    def MTEConnect(self, params):
        sParams = '\n'.join(['{0}={1}'.format(str(k), str(v)) for (k,v) in params.items()])
        #self.debug(sParams)
        self._Idx = self._lib.MTEConnect(sParams.encode('utf-8'), self._ErrorMsg)
        return self._Idx

    def isConnect(self):
        return (self._Idx >= ASTS.MTE_OK)

    def printConnectStatus(self):
        print('ASTS Bridge Connect Status: ', end='')
        if self.isConnect():
            print('Connected.')
        else:
            print('Connect error (%d): %s' %(self._Idx, self.ErrorMsg()))

    #int32_t MTEDisconnect(int32_t conno);
    def MTEDisconnect(self):
        return self._lib.MTEDisconnect(self._Idx)

    #int32_t MTEGetServInfo(int32_t conno, char **buffer, int32_t *len);
    @Metrics()
    def MTEGetServInfo(self):
        _si = POINTER(c_char)()
        _len = c_int32()
        self.ServInfo = None
        res = self._lib.MTEGetServInfo(self._Idx, byref(_si), byref(_len))
        if res != ASTS.MTE_OK:
            return res

        ServInfo = cast(_si, POINTER(c_char * _len.value))
        self._InitServInfo()
        offset = 0
        for f in self.ServInfo:
            if self.ServInfo[f]['type'] == c_int:
                _val = int.from_bytes(ServInfo.contents[offset:offset + self.ServInfo[f]['size']], byteorder='little', signed=True)
                offset += self.ServInfo[f]['size']
            elif self.ServInfo[f]['type'] == c_char_p:
                if self.ServInfo[f]['size'] > 0:
                    _val = c_char_p(ServInfo.contents[offset:offset + self.ServInfo[f]['size']]).value.decode('cp1251')
                    offset += self.ServInfo[f]['size']
                else:
                    _val = c_char_p(ServInfo.contents[offset:_len.value]).value.decode('cp1251')
                    offset += len(_val) + 1
            elif self.ServInfo[f]['type'] == c_char:
                _val = ServInfo.contents[offset:offset + 1].decode('cp1251')
                offset += 1
            self.ServInfo[f] = _val

        return res

    #int32_t MTEConnectionStatus(int32_t conno);
    def MTEConnectionStatus(self):
        return self._lib.MTEConnectionStatus(self._Idx)
    
    #int32_t MTEConnectionStats(int32_t conno, ConnectionStats *stats)
    def MTEConnectionStats(self):
        self.ConnStats.Size = sizeof(ASTS.ConnectionStats)
        return self._lib.MTEConnectionStats(self._Idx, self.ConnStats)

    #int32_t MTESelectBoards(int32_t conno, const char *boards, char *result);
    #@Metrics()
    def MTESelectBoards(self, _boards):
        _resMsg = create_string_buffer(256)
        res = self._lib.MTESelectBoards(self._Idx, _boards.encode('utf-8'), _resMsg)
        return (res, _resMsg.value.decode('cp1251') if res in ASTS.MTE_TRANSPROCESSED else '')

    #int32_t MTEStructure(int32_t conno, MTEMSG **msg);
    #@Metrics()
    def MTEStructure(self):
        res = self._lib.MTEStructure(self._Idx, self._mtemsg.pointer())
        self._mtemsg.toMTEStructure(res, 1)
        return res

    #int32_t MTEStructure2(int32_t conno, MTEMSG **msg);
    #@Metrics()
    def MTEStructure2(self):
        res = self._lib.MTEStructure2(self._Idx, self._mtemsg.pointer())
        self._mtemsg.toMTEStructure(res, 2)
        return res

    # int32_t __callspec MTEStructureEx(int32_t conno, int32_t version, MTEMSG **msg);
    #@Metrics()
    def MTEStructureEx(self, _version):
        res = self._lib.MTEStructureEx(self._Idx, _version, self._mtemsg.pointer())
        self._mtemsg.toMTEStructure(res, _version)
        return res

    #int32_t MTEOpenTable(int32_t conno, const char *name, const char *params, int32_t complete, MTEMSG **msg);
    @Metrics()
    def MTEOpenTable(self, _table, _params, _complete):
        if not self._mtemsg.isMTEStructure():
            _res = self.MTEStructure2()
            if _res != ASTS.MTE_OK:
                return res
        Metrics.startMetric('lib.MTEOpenTable')
        _res = self._lib.MTEOpenTable(self._Idx, _table.encode('utf-8'), _params.encode('utf-8'), _complete, self._mtemsg.pointer())
        Metrics.stopMetric()
        self._mtemsg.toMTETable(_res, _table)

        return _res

    #int32_t MTEAddTable(int32_t conno, int32_t tabno, int32_t ref);
    #@Metrics()
    def MTEAddTable(self, _tabno, _ref=None):
        if isinstance(_tabno, str):
            _tabno = self._mtemsg.findTable(_tabno)

        if _tabno < self.MTE_OK:
            return _tabno

        #Metrics.startMetric('lib.MTEAddTable')
        _res = self._lib.MTEAddTable(self._Idx, _tabno, _tabno)
        #Metrics.stopMetric()

    #int32_t MTERefresh(int32_t conno, MTEMSG **msg);
    @Metrics()
    def MTERefresh(self):
        Metrics.startMetric('lib.MTERefresh')
        _res = self._lib.MTERefresh(self._Idx, self._mtemsg.pointer())
        Metrics.stopMetric()
        if _res != self.MTE_OK:
            return _res
        self._mtemsg.toMTETables(_res)

    #int32_t MTECloseTable(int32_t conno, int32_t tabno);
    @Metrics()
    def MTECloseTable(self, _tabno):
        if isinstance(_tabno, str):
            _tabno = self._mtemsg.findTable(_tabno)

        self._mtemsg.closeMTETable(_tabno)
        return self._lib.MTECloseTable(self._Idx, _tabno)

    def TableData(self, _table):
        return self._mtemsg.TableData(_table)

    #int32_t MTEFreeBuffer(int32_t conno);
    @Metrics()
    def MTEFreeBuffer(self):
        return self._lib.MTEFreeBuffer(self._Idx)

'''
int32_t MTEExecTransEx(int32_t conno, const char *name, const char *params, int32_t clientIP, MteTransResult *result);

int32_t MTEExecTrans(int32_t conno, const char *name, const char *params, char *error);
int32_t MTEExecTransIP(int32_t conno, const char *name, const char *params, char *error, int32_t clientIP);

int32_t MTEGetSnapshot(int32_t conno, char **buffer, int32_t *len);
int32_t MTESetSnapshot(int32_t conno, const char *buffer, int32_t len, char *error);

int32_t MTEGetExtData(int32_t conno, const char *DataSetName, const char *ExtFileName, MTEMSG **msg);
int32_t MTEGetExtDataRange(int32_t conno, const char *DataSetName, const char *ExtFileName,
                                     uint32_t DataOffset, uint32_t DataSize, MTEMSG **msg);


int32_t MTEGetTablesFromSnapshot(int32_t conno, const char* snapshot, int32_t len, MteSnapTable** tables);
int32_t MTEOpenTableAtSnapshot(int32_t conno, const char *name, const char *params, const char *snapshot, int32_t len, MTEMSG **msg);
'''
if __name__ == '__main__':
    asts = ASTS(DEBUG=True)
    print(asts.MTEGetVersion())
    asts.MTEConnect({
        'PACKETSIZE': '60000',
        'INTERFACE': 'IFCBroker40',
        'SERVER': 'UAT_GATEWAY',
        'SERVICE': '16411/16412',
        'BROADCAST': '91.208.232.211',
        'USERID': 'MU9050300002',
        'PASSWORD': '6204',
        'LANGUAGE': ASTS.LANGUAGE_RUS,
        'LOGFOLDER': os.path.dirname(os.path.abspath(__file__)) + '/log/',
        'LOGGING': '2,2',
        'LOGLEVEL': '30',
        #'BOARDS': 'TQCB',
#        'BOARDS': 'TQCB,PSAU,PSBB,TQIR,TQBR,TQPI',
    })
    asts.printConnectStatus()

    res = asts.MTEGetServInfo()
    print('MTEGetServInfo (%d): %s' %(res, asts.MTEErrorMsg(res)))
    '''
    print(json.dumps(asts.ServInfo, skipkeys=True, ensure_ascii=False, indent=2))

    res = asts.MTEConnectionStatus()
    print('MTEConnectionStatus (%d): %s' %(res, asts.MTEErrorMsg(res)))

    res = asts.MTEConnectionStats()
    print('MTEConnectionStats (%d): %s' %(res, asts.MTEErrorMsg(res)))
    
    res = asts.MTEStructure()
    print('MTEStructure (%d): %s' %(res, asts.MTEErrorMsg(res)))
    '''
    '''
    res = asts.MTEStructure2()
    print('MTEStructure2 (%d): %s' %(res, asts.MTEErrorMsg(res)))
    print(json.dumps(asts._mtemsg.MTEStructure['Таблицы'], skipkeys=False, ensure_ascii=False, indent=2))
    '''
    '''
    with open('MTEStructure.json', 'w') as fp:
        json.dump(asts._mtemsg.MTEStructure, fp=fp, skipkeys=False, ensure_ascii=False, indent=4)
    '''

    '''
    res = asts.MTEStructureEx(2)
    print('MTEStructureEx (%d): %s' %(res, asts.MTEErrorMsg(res)))

    res = asts.MTESelectBoards('TQIR')
    #res = asts.MTESelectBoards('CETS')
    print('MTESelectBoards (%d): %s (%s)' %(res[0], asts.MTEErrorMsg(res[0]), res[1]))
    '''
    def printTableData(table, rowMax=None):
        tb = asts.TableData(table)
        rT = [ ('     ', 5, 'row'), ]
        for fl in tb['fields']:
            _len = max(len(fl['name']), fl['size'])
            rT.append( (('{0:^%ds}' %_len).format(fl['name']), _len, fl['name']) )
        print('|'.join(map(lambda x: x[0], rT)))

        rwc = 1
        for rw in tb['rows']:
            if rowMax is not None and rwc > rowMax:
                break
            r = [ (('{0:>%dd}' %rT[0][1]).format(rwc))]
            for fl in range(1, len(rT)):
                r.append( ('{0:%ds}' %rT[fl][1]).format(rw[rT[fl][2]] if rT[fl][2] in rw else '') )
            print('|'.join(r))
            rwc += 1

    #for tbn in ('TRDTIMETYPES', 'TRDTIMEGROUPS', 'TRADETIME'):
    for tbn in ('TESYSTIME', ):
        res = asts.MTEOpenTable(tbn, '', True)
        if res < asts.MTE_OK:
            print('MTEOpenTable (%d): %s <%s>' % (res, asts.MTEErrorMsg(res), asts.MSGError()))
            continue
        printTableData(tbn)
    #exit(0)

    Metrics.noPrint = True
    boards = [ ('PSAU,PSBB', 'bonds-first'), ('TQCB,TQIR,TQOB,TQRD', 'bonds-second'), ('SNDX,RTSI', 'indexes'), ('CETS', 'currencies'), ('TQBR,TQPI,TQIF,TQTF', 'shares') ]
    boards.append((','.join(map(lambda x: str(x[0]), boards)), 'all'))
    for br in boards:
    #for br in ('TQCB', ):
        res = asts.MTESelectBoards(br[0])
        if res[0] != asts.MTE_OK:
            print('MTESelectBoards(%s) (%d): %s (%s)' % (br[0], res[0], asts.MTEErrorMsg(res[0]), res[1]))
            continue
        for comp in (True, False):
            res = asts.MTEOpenTable('SECURITIES', '        ', comp)
            if res < asts.MTE_OK:
                print('MTEOpenTable (%d): %s <%s>' %(res, asts.MTEErrorMsg(res), asts.MSGError()))
                break
            key = 'SECURITIES.{0:s}.{1:s}.{2:s}'.format(br[0], str(comp), br[1])
            Metrics.Var[key] = [(Metrics.Var[Metrics.VAR_LE], Metrics.Var['LastRead']), ]
            #printTableData('SECURITIES', rowMax=100)
            #exit(0)

            for i in range(1, 100):
                Metrics.info('Iteration: %d' %i)
                asts.MTEAddTable('SECURITIES')
                asts.MTERefresh()
                if Metrics.Var['LastRead'] < 5:
                    break
                Metrics.Var[key].append((Metrics.Var[Metrics.VAR_LE], Metrics.Var['LastRead']))
                time.sleep(0.2)
            asts.MTECloseTable('SECURITIES')

    for key in Metrics.Var:
        if not key.startswith('SECURITIES'):
            continue
        k = key.split('.', 4)
        print('Boards: %s (%s). OpenTable Complete=%s' %(k[1], k[3], k[2]))
        totalRead = 0
        for i in range(len(Metrics.Var[key])):
            print('{0:>2d}: Execute {1:>8.3f} ms. Read {2:>10,d} bytes'.format(i, Metrics.Var[key][i][0] / 1e6, Metrics.Var[key][i][1]))
            totalRead += Metrics.Var[key][i][1]
        print('{0:s}\n{1:<28s} {2:>11,d} bytes\n'.format('-' * 46, 'Total read', totalRead))
    '''
    if res >= ASTS.MTE_OK:
        with open('MTEOpenTable.json', 'w') as fp:
            json.dump(asts._mtemsg.MTETables, fp=fp, skipkeys=False, ensure_ascii=False, indent=4)
    '''