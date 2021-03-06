import time
import shlex
import subprocess
import threading
import netifaces
from wdln.settings import IBP_CONFIG
from wdln.ferry.log import log

class IBPWatcher:    
    def __init__(self, cfg=IBP_CONFIG):
        self.cfg = cfg
        self.addrs = self._get_addrs()
        self.first = True
                
        th = threading.Thread(
            name='ibp_iface',
            target=self._watcher,
            daemon=True,
            args=(cfg,)
        )
        th.start()

    def _get_addrs(self):
        naddrs = []
        for i in netifaces.interfaces():
            addrs = netifaces.ifaddresses(i)
            if netifaces.AF_INET in addrs:
                naddrs.append(addrs[netifaces.AF_INET][0]['addr'])
        return naddrs
        
    def _watcher(self, cfg):
        while True:
            naddrs = self._get_addrs()
            if set(naddrs) != set(self.addrs) or self.first:
                log.debug("iface diff: {}".format(set(naddrs) - set(self.addrs)))
                istr = ""
                for i in naddrs:
                    istr+="{}:6714;".format(i)
                self.addrs = naddrs
                self.update_ibp_server(istr)
                self.first = False

            time.sleep(5)

    def update_ibp_server(self, istr):
        cmdstr = "sudo sed -i 's/^interfaces=.*$/interfaces="+istr+"/g' "+self.cfg
        subprocess.run(shlex.split(cmdstr))
        cmdstr = "sudo /etc/init.d/ibp-server restart"
        subprocess.run(shlex.split(cmdstr), stdout=subprocess.DEVNULL)
        log.info("Detected interface change, restarted ibp-server") 
        
