#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import win32service  
import win32serviceutil  
import win32event  
  
class PySvc(win32serviceutil.ServiceFramework):  
    _svc_name_ = "PySvc"  
    _svc_display_name_ = "Python Test Service"  
    _svc_description_ = "This service writes stuff to a file"  
      
    def __init__(self, args):  
        win32serviceutil.ServiceFramework.__init__(self,args)  
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)  
      
    def SvcDoRun(self):  
        import servicemanager  
          
        rc = None  
        while rc != win32event.WAIT_OBJECT_0:  
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)  
              
    def SvcStop(self):  
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)  
        win32event.SetEvent(self.hWaitStop)  
          
if __name__ == '__main__':  
    win32serviceutil.HandleCommandLine(PySvc)  
