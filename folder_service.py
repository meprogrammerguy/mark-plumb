#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import win32service  
import win32serviceutil  
import win32event 
import tempfile 
  
class PySvc(win32serviceutil.ServiceFramework):  
    _svc_name_ = "folder_service"  
    _svc_display_name_ = "Python Stock Polling Service"  
    _svc_description_ = "This service polls for the latest stock quotes"  
      
    def __init__(self, args):  
        win32serviceutil.ServiceFramework.__init__(self,args)  
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)  
      
    def SvcDoRun(self):  
        import servicemanager

        log = {}
        log['status'] = "start"
        log['pid'] = os.getpid()
        log['working directory'] = os.getcwd()
        log['username'] = getpass.getuser()
        plumb.LogDaemon(log, False)
        rc = None
        ticks = -1
        while rc != win32event.WAIT_OBJECT_0:
            plumb.Holiday(False)
            defaults, types = plumb.GetDefaults(False)
            pm = 0
            if (defaults['poll minutes'] is None):
                pm = 10
            else:
                pm = defaults['poll minutes']
            log['poll minutes'] = dm
            tick_max = pm * 60
            if (ticks == -1):
                ticks = tick_max + 1
            if (ticks > tick_max):
                do_something(defaults)
                ticks = 0
            ticks += 1
            if (ticks == 1):
                log['status'] = 'sleep'
                plumb.LogDaemon(log, False)  
            rc = win32event.WaitForSingleObject(self.hWaitStop, 1000)  
              
    def SvcStop(self):  
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING) 
        log = {}
        log['status'] = "stop"
        log['pid'] = os.getpid()
        log['working directory'] = os.getcwd()
        log['username'] = getpass.getuser()
        plumb.LogDaemon(log, False) 
        win32event.SetEvent(self.hWaitStop)  
          
def do_something(defaults):
    log = {}
    log['status'] = "wake"
    log['pid'] = os.getpid()
    log['working directory'] = os.getcwd()
    log['username'] = getpass.getuser()
    df = ""
    if (defaults['folder name'] is None):
        log['status'] = 'error'
        log['content'] = "folder name is missing in defaults, cannot continue"
        plumb.LogDaemon(log, False)
        break
    else:
        df = plumb.GetDB(False)
    log['dbase name'] = df
    plumb.LogDaemon(log, False)
    if plumb.DayisOpen(False) and (not plumb.DayisClosed(False)):
        log['open'] = defaults['open']
        log['final poll'] = time.ctime()
        log['status'] = 'open'
        plumb.LogDaemon(log, False)
        try:
            result, resultError = plumb.Update(False)
            if not result:
                if resultError > "":
                    log['status'] = 'error'
                    log['content'] = resultError
                    plumb.LogDaemon(log, False)
            else:
                log['status'] = 'success'
                plumb.LogDaemon(log, False)
        except Exception as e:
            log['status'] = 'exception'
            log['content'] = exceptionError
            plumb.LogDaemon(log, False)
    else:
        log['close'] = defaults['close']
        log['final poll'] = time.ctime()
        log['status'] = 'closed'
        plumb.LogDaemon(log, False)

if __name__ == '__main__':  
    win32serviceutil.HandleCommandLine(PySvc)  
