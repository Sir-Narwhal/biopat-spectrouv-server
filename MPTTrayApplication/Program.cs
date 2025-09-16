using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Runtime.Remoting.Messaging;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using MPTSaveSpectrumLibrary;


namespace MPTTrayApplication
{
    
    static class Program
    {

        private static NotifyIcon trayIcon;
        private static ToolStripMenuItem statusItem;
        private static CancellationTokenSource cts;
        private static SynchronizationContext uiContext;



        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            RedisManager.Init();

            uiContext = SynchronizationContext.Current;


            // --- Setup Tray Icon ---
            trayIcon = new NotifyIcon
            {
                Icon = System.Drawing.Icon.ExtractAssociatedIcon(Application.ExecutablePath),
                Visible = true,
                Text = "Initializing..."
            };

            // --- Setup Context Menu ---
            ContextMenuStrip menu = new ContextMenuStrip();
            statusItem = new ToolStripMenuItem("Status: Initializing...");
            menu.Items.Add(statusItem);
            menu.Items.Add("Exit", null, (s, e) => ExitApp());
            trayIcon.ContextMenuStrip = menu;

            // --- Start background worker ---
            cts = new CancellationTokenSource();
            Task.Run(() => StatusWorker(cts.Token));

            //using (NotifyIcon trayIcon = new NotifyIcon())
            //{
            //    Stream iconStream = System.Reflection.Assembly.GetExecutingAssembly().GetManifestResourceStream("MPTTrayApplication.SpectroUV.ico");

            //    if (iconStream != null)
            //    {
            //        trayIcon.Icon = new Icon(iconStream);
            //    }
            //    else
            //    {
            //        Console.WriteLine("Failed to load icon resource.");
            //        trayIcon.Icon = SystemIcons.Application; // Fallback icon
            //    }

            //    trayIcon.Visible = true;
            //    trayIcon.Text = "MPT Controller";

            //    trayIcon.BalloonTipTitle = "Status Update";
            //    trayIcon.BalloonTipText = "Tec5 MPT automation is ready.";
            //    trayIcon.BalloonTipIcon = ToolTipIcon.Info;
            //    trayIcon.ShowBalloonTip(3000); // show for 3 seconds

            //    ContextMenuStrip menu = new ContextMenuStrip();
            //    ToolStripMenuItem statusItem = new ToolStripMenuItem("Status: Initializing...");
            //    menu.Items.Add(statusItem);
            //    menu.Items.Add("Exit", null, (s, e) => Application.Exit());
            //    trayIcon.ContextMenuStrip = menu;

            Task.Run(() => WorkerLoop());
            Application.Run();
               
            //}
            //Application.Run(new Form1());

        }
        private static void ExitApp()
        {
            cts.Cancel();
            trayIcon.Visible = false;
            RedisManager.Dispose();
            Application.Exit();
        }

        private static void OnExit(object sender, EventArgs e)
        {
            Console.WriteLine("Shutting down gracefully...");
            RedisManager.Dispose(); 
        }

        static async Task WorkerLoop()
        {

            MPTLogic logicDriver = new MPTLogic(); 
            CancellationTokenSource cts = new CancellationTokenSource();
            
            logicDriver.RedisSetup();
            await Task.Delay(1000);

            SaveSpectrumUIHelper.StartProgram();
            await Task.Delay(1000); 

            while (true)
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
                await Task.Delay(200);
            }
            return;
        }


        private static async Task StatusWorker(CancellationToken token)
        {
            string redisStatus = "";

            while (!token.IsCancellationRequested)
            {
                try
                {
                    // Example: read a key called "AutomationStatus"
                    string stopState = RedisManager.GetString("mpt_stop_state") ?? "Error: Stop";
                    string startState = RedisManager.GetString("mpt_start_state") ?? "Error: Start";

                    bool stopStateSucess = bool.TryParse(stopState, out bool stopStateBool);
                    bool startStateSucess = bool.TryParse(startState, out bool startStateBool);

                    if (stopStateBool)
                    {
                        redisStatus = "Stopped";
                    }
                    else if (startStateBool)
                    {
                        redisStatus = "Running";
                    }
                    else
                    {
                        redisStatus = "Error";
                    }

                    // Update tray icon tooltip & context menu safely
                    uiContext?.Post(_ =>
                    {
                        trayIcon.Text = $"Status: {redisStatus}";
                        if (statusItem != null)
                            statusItem.Text = $"Status: {redisStatus}";
                    }, null);
                }
                catch (Exception ex)
                {
                    uiContext?.Post(_ =>
                    {
                        trayIcon.Text = $"Status: Error";
                        if (statusItem != null)
                            statusItem.Text = $"Status: {ex.Message}";
                    }, null);
                }

                await Task.Delay(1000, token); // poll every second
            }
        }
    }
}
