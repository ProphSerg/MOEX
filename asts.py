from ctypes import *
import os
import json
import mtemsg

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
        self.ConnStats = ASTS.ConnectionStats()

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
        self._lib.MTEConnectionStats.argtypes = [c_int32, POINTER(ASTS.ConnectionStats)]
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


    def ErrorMsg(self):
        return self._ErrorMsg.value.decode('cp1251')

    #char* MTEGetVersion();
    def MTEGetVersion(self):
        return self._lib.MTEGetVersion().decode('utf-8')

    #char* MTEErrorMsg(int32_t code);
    def MTEErrorMsg(self, code):
        return self._lib.MTEErrorMsg(code).decode('utf-8')

    #char* MTEErrorMsgEx(int32_t code, const char *language);
    def MTEErrorMsgEx(self, code, lang=LANGUAGE_ENG):
        return self._lib.MTEErrorMsgEx(code, lang.encode('utf-8')).decode('utf-8')

    #int32_t MTEConnect(const char *params, char *error);
    def MTEConnect(self, params):
        sParams = '\n'.join(['{0}={1}'.format(str(k), str(v)) for (k,v) in params.items()])
        self.debug(sParams)
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
    def MTESelectBoards(self, _boards):
        _resMsg = create_string_buffer(256)
        res = self._lib.MTESelectBoards(self._Idx, _boards.encode('utf-8'), _resMsg)
        return (res, _resMsg.value.decode('cp1251') if res in ASTS.MTE_TRANSPROCESSED else '')

    #int32_t MTEStructure(int32_t conno, MTEMSG **msg);
    def MTEStructure(self):
        _msg = mtemsg.MTEMSG()
        res = self._lib.MTEStructure(self._Idx, _msg.pointer())
        return (res, _msg.toMTEStructure(res, 1))

    #int32_t MTEStructure2(int32_t conno, MTEMSG **msg);
    def MTEStructure2(self):
        #self._lib.MTEStructure2.argtypes = [c_int32, POINTER(c_char *8)]
        _msg = mtemsg.MTEMSG()
        res = self._lib.MTEStructure2(self._Idx, _msg.pointer())
        return (res, _msg.toMTEStructure(res, 2))

    # int32_t __callspec MTEStructureEx(int32_t conno, int32_t version, MTEMSG **msg);
    def MTEStructureEx(self, _version):
        _msg = mtemsg.MTEMSG()
        res = self._lib.MTEStructureEx(self._Idx, _version, _msg.pointer())
        return (res, _msg.toMTEStructure(res, _version))

'''
int32_t MTEExecTransEx(int32_t conno, const char *name, const char *params, int32_t clientIP, MteTransResult *result);

int32_t MTEExecTrans(int32_t conno, const char *name, const char *params, char *error);
int32_t MTEExecTransIP(int32_t conno, const char *name, const char *params, char *error, int32_t clientIP);

int32_t MTEOpenTable(int32_t conno, const char *name, const char *params, int32_t complete, MTEMSG **msg);
int32_t MTEAddTable(int32_t conno, int32_t tabno, int32_t ref);
int32_t MTERefresh(int32_t conno, MTEMSG **msg);
int32_t MTECloseTable(int32_t conno, int32_t tabno);
int32_t MTEFreeBuffer(int32_t conno);

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
        'LANGUAGE': ASTS.LANGUAGE_ENG,
        'LOGFOLDER': os.path.dirname(os.path.abspath(__file__)) + '/log/',
        'LOGGING': '4,2',
        'LOGLEVEL': '30',
        'BOARDS': 'TQCB',
    })
    asts.printConnectStatus()
    '''
    res = asts.MTEGetServInfo()
    print('MTEGetServInfo (%d): %s' %(res, asts.MTEErrorMsg(res)))
    print(json.dumps(asts.ServInfo, skipkeys=True, ensure_ascii=False, indent=2))

    res = asts.MTEConnectionStatus()
    print('MTEConnectionStatus (%d): %s' %(res, asts.MTEErrorMsg(res)))

    res = asts.MTEConnectionStats()
    print('MTEConnectionStats (%d): %s' %(res, asts.MTEErrorMsg(res)))
    
    res = asts.MTEStructure()
    print('MTEStructure (%d): %s' %(res[0], asts.MTEErrorMsg(res[0])))
    '''
    res = asts.MTEStructure2()
    print('MTEStructure2 (%d): %s' %(res[0], asts.MTEErrorMsg(res[0])))
    print(json.dumps(res[1]['Таблицы'], skipkeys=False, ensure_ascii=False, indent=2))
    '''
    res = asts.MTEStructureEx(2)
    print('MTEStructureEx (%d): %s' %(res[0], asts.MTEErrorMsg(res[0])))

    res = asts.MTESelectBoards('TQIR')
    #res = asts.MTESelectBoards('CETS')
    print('MTESelectBoards (%d): %s (%s)' %(res[0], asts.MTEErrorMsg(res[0]), res[1]))
    '''