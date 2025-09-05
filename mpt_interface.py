''' 
_win32_background_trial.py 

@author:        Joel Baarbe


This is the testing ground for developing the code required to interact with the TecSaas MPT software
    using python via pywinauto debug counsel 

'''

import os 
import sys
import time
import traceback 
import psutil
import gc 

import clr 

sys.path.append(os.path.abspath(r'.\cslibraries'))

clr.AddReference("MPTSaveSpectrumLibrary")

from MPTSaveSpectrumLibrary import SaveSpectrumUIHelper
from MPTSaveSpectrumLibrary import WindowForceCloser


class MPTInterface(): 
    '''
    class:          MPTInterface 

    @author:        Joel Baarbe 
    @date:          01/23/2025

    This class will connect with the TecSaas MPT Program, provide the framework to modify the program, and allow
        the spectra to be saved in a timely fashion (less than 500 ms). 

    This class can only handle one channel. 
    
    '''

    def __init__(self, debug_logger, **kwargs): 
        '''
        Method:                 MPTIterface.__init__ 

        @author:                Joel Baarbe 

        Initialization method for class MPTItnerface. Essential attributes are defined here without need for 
            specification by the user. 
        '''
        self.debug_logger = debug_logger
        self.start()
        
    def start(self):
        '''
        Method:                 MPTInterface.start

        @author:                Joel Baarbe
        @date:                  05/08/2025

        This method will start the MPT program

        '''

        self.ready = SaveSpectrumUIHelper.StartProgram()
        self.pid = SaveSpectrumUIHelper.GetProgramId()
        self.retries = 10
        
        counter = 0 
        
        while self.ready != True: 
            # Do something 
            try: 
                SaveSpectrumUIHelper.ConnectDevice(self.pid) 
                time.sleep(5) 
            except: 
                time.sleep(2) 
                counter += 1

            self.ready = SaveSpectrumUIHelper.IsReady(self.pid) 
            print(f"Program is not ready") 
            self.debug_logger.warning(f"Program is not ready")

            if counter > self.retries:
                print(f"Program cannot get to ready state after {self.retries} tries")
                self.debug_logger.warning(f"Program cannot get to ready state after {self.retries} tries. Restarting Program")

                SaveSpectrumUIHelper.RestartProgram()
                self.ready = SaveSpectrumUIHelper.StartProgram()
                self.pid = SaveSpectrumUIHelper.GetProgramId()

                counter = 0



    def kill(self): 
        '''
        Method:                 MPTInterface.kill 

        @author:                Joel Baarbe 
        @date:                  02/06/2025

        This method will kill the program, so that it can be restarted. 

        '''
        
        SaveSpectrumUIHelper.RestartProgram()

    # def 
    
    def savespectrum(self, savename): 
        '''
        Method:                 MPTInterface.savespectrum

        @author:                Joel Baarbe/ 
        @date:                  01/23/2025

        This method will save the spectrum file to the indicated director with the name provided.        
        
        '''

        try: 
            WindowForceCloser.ForceCloseSaveAsDialogs() 
            SaveSpectrumUIHelper.FillSaveAsDialog(self.pid, savename)
        except Exception as e: 
            print(f"Python caught exception from c# .dll:\t{e}")
            print(traceback.format_exc())
            self.debug_logger.error(f"Python caught exception from c# .dll:\t{e}")
        # try: 
        #     # SaveSpectrumUIHelper.ClickControl(self.pid, "automationid", "ExportButton")
        #     # savename = os.path.join(os.path.abspath(filedir), filename)
        #     # print(f"Savename:\t{savename}") 
        #     SaveSpectrumUIHelper.FillSaveAsDialog(self.pid, savename)
        #     print(f"Clicking Save Spectrum Successful") 

        # except: 
        #     print(f"Failed Clicking Save Spectrum ") 
        #     exit() 

    def garbage_collect(self): 
        '''
        Method:         MPTInterface.garbage_collect

        @author:        Joel Baarbe 
        @date:          04/08/2025 

        This function will do a garbage collection. 
            
        '''
        gc.collect() 
        SaveSpectrumUIHelper.ForceGC() 
        


def test_spectrum_time(): 
    x = MPTInterface() 

    times = [] 
    # while True: 
    for loop in range(50): 
        starttime = time.time() 
        x.savespectrum(os.path.abspath(os.path.join("temp_data", "helloworld.txt"))) 
        endtime = time.time() - starttime
        times.append(endtime) 

    print(times) 


def monitor_memory(pid, debug_logger): 
    '''
    Function:       montior_memory

    @author:        Joel Baarbe 
    @date:          04/08/2025

    This function will monitor the memory of the MPT software and 
        report the total memory used. 

    This is a diagnostic tool. 
    
    '''

    process = psutil.Process(pid) 
    mem = process.memory_info().rss/1024/1024 

    print(f"Memory Usage: {mem:.2f} MB") 
    debug_logger.info(f"Memory Usage: {mem:.2f} MB")  


if __name__ == "__main__":
    test_spectrum_time()
   
