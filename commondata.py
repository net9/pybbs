import struct
from sysv_ipc import SharedMemory, ExistentialError

from Util import Util
import UtmpHead
from Log import Log
import Config

'''
struct public_data {
    time_t nowtime;
    int sysconfimg_version;
    int www_guest_count;
    unsigned int max_user;
    unsigned int max_wwwguest;
#ifdef FLOWBANNER
        int bannercount;
        char banners[MAXBANNER][BANNERSIZE];
#else
    char unused[1004];
#endif
};
'''

NOWTIME_POS = 0
SYSCONFIMG_VERSION_POS = NOWTIME_POS + 4
WWW_GUEST_COUNT_POS = SYSCONFIMG_VERSION_POS + 4
MAX_USER_POS = WWW_GUEST_COUNT_POS + 4
MAX_WWWGUEST_POS = MAX_USER_POS + 4
UNUSED_POS = MAX_WWWGUEST_POS + 4

PUBLICSHM_SIZE = UNUSED_POS + 1004

class CommonData:
    parser = struct.Struct('=iiiII')
    _fields = ['nowtime', 'sysconfimg_version', 'www_guest_count', 'max_user', 'max_wwwguest']
    uidshm = None

    @staticmethod
    def GetWWWGuestCount():
        return Util.SHMGetInt(CommonData.publicshm, WWW_GUEST_COUNT_POS)

    @staticmethod
    def GetMaxUser():
        return Util.SHMGetUInt(CommonData.publicshm, MAX_USER_POS)

    @staticmethod
    def SetMaxUser(max_user):
        return Util.SHMPutUInt(CommonData.publicshm, MAX_USER_POS, max_user)

    @staticmethod
    def GetMaxWWWUser():
        return Util.SHMGetUInt(CommonData.publicshm, MAX_WWWGUEST_POS)

    @staticmethod
    def SetMaxWWWUser(max_www):
        return Util.SHMSetUInt(CommonData.publicshm, MAX_WWWGUEST_POS, max_www)

    @staticmethod
    def SaveMaxUser():
        CommonData.SetMaxUser(UtmpHead.UtmpHead.GetNumber() + CommonData.GetWWWGuestCount())
        CommonData.SetMaxWWWGuest(CommonData.GetWWWGuestCount())
        with open(Config.BBS_ROOT + "etc/maxuser", "w") as fmaxuser:
            fmaxuser.write("%d %d" % (CommonData.GetMaxUser(), CommonData.GetMaxWWWGuest()))

    @staticmethod
    def UpdateMaxUser():
        if (UtmpHead.UtmpHead.GetNumber() + CommonData.GetWWWGuestCount() > CommonData.GetMaxUser()):
            CommonData.SetReadonly(0)
            CommonData.SaveMaxUser()
            CommonData.SetReadonly(1)

    @staticmethod
    def Init():
        if (CommonData.publicshm == None):
            try:
                CommonData.publicshm = SharedMemory(Config.PUBLIC_SHMKEY, size = PUBLICSHM_SIZE)
            except ExistentialError:
                Log.Error("time daemon not started")
                raise Exception("Initialization failed: publicshm not created")

    @staticmethod
    def SetReadonly(readonly):
        CommonData.publicshm.detach()
        CommonData.publicshm.attach(None, (sysv_ipc.SHM_RDONLY if readonly else 0))

