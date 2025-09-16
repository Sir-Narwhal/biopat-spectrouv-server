using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Linq;
using System.ServiceProcess;
using System.Text;
using System.Threading; 
using System.Threading.Tasks;
using MPTSaveSpectrumLibrary;
using MPTControlService;

namespace MPTControlService
{
    public partial class MPTControl : ServiceBase
    {
        private Thread workerThread;
        private bool running;
        private MPTLogic logicDriver;



        public MPTControl()
        {
            InitializeComponent();
        }


        //bool restartBool;
        //bool refreshBool;
        //bool stopBool;
        //bool startBool; 

        protected override void OnStart(string[] args)
        {
            RedisManager.Init();

            logicDriver = new MPTLogic(); 

            logicDriver.RedisSetup();

            running = true;
            workerThread = new Thread(WorkerLoop);
            workerThread.IsBackground = true;
            workerThread.Start();
            SaveSpectrumUIHelper.StartConnectMonitor();
            Thread.Sleep(10000); 
        }

       

        private void WorkerLoop()
        {
            CancellationTokenSource cts = new CancellationTokenSource();

            while (running)
            {
                try
                {
                    // put logic for controller 
                    var tasks = new List<Task>
                    {
                        Task.Run(() => logicDriver.StartLogic()),
                        Task.Run(() => logicDriver.StopLogic()),
                        Task.Run(() => logicDriver.RefreshLogic()),
                        Task.Run(() => logicDriver.RestartLogic())
                    };
                    Task.WaitAll(tasks.ToArray());
                    Console.WriteLine("[WorkerLoop] Ran all tasks sucessfully."); 

                }
                catch (OperationCanceledException)
                {
                    Console.WriteLine("[WorkerLoop] Operation was Cancelled. Exiting Loop");
                    break; 
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"[WorkerLoop] Error encountered: {ex.Message}"); 
                }
                Task.Delay(1000); 
            }
            return; 
        }

        

        protected override void OnStop()
        {
            RedisManager.Dispose();
            running = false;
            workerThread?.Join(); 
        }
    }
}
