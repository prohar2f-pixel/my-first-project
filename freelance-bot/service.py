import sys
import os
import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess

class BotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "FreelanceBot"
    _svc_display_name_ = "Freelance Monitor Bot"
    _svc_description_ = "Мониторит заказы на FL.ru, Habr, Kwork и Telegram"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            self.process.terminate()
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        self.process = subprocess.Popen(
            [sys.executable, os.path.join(bot_dir, "main.py")],
            cwd=bot_dir
        )
        self.process.wait()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(BotService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(BotService)
