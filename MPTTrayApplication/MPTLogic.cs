using MPTSaveSpectrumLibrary;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace MPTTrayApplication
{
    public class MPTLogic
    {
        public string mptStop = "mpt_stop";
        public string mptRefresh = "mpt_refresh";
        public string mptRestart = "mpt_restart";
        public string mptStart = "mpt_start";

        public void RedisSetup()
        {
            RedisManager.SetString(mptStop, "false");
            RedisManager.SetString(mptStart, "false");
            RedisManager.SetString(mptRestart, "false");
            RedisManager.SetString(mptRefresh, "false");

            RedisManager.SetString($"{mptStop}_state", "false");
            RedisManager.SetString($"{mptStart}_state", "true");
            RedisManager.SetString($"{mptRestart}_state", "false");
            RedisManager.SetString($"{mptRefresh}_state", "false");
        }
        public async Task RestartLogic()
        {
            string restartString = RedisManager.GetString(mptRestart);
            bool restartBoolSuccess = bool.TryParse(restartString, out bool restartBool);

            try
            {
                Console.WriteLine($"Restart Bool fulfilled: {restartBool}");

                if (restartBool)
                {
                    SaveSpectrumUIHelper.RestartProgram();
                    await Task.Delay(5000); 
                    SaveSpectrumUIHelper.StartProgram();

                    RedisManager.SetString($"{mptRestart}_state", Convert.ToString(!restartBool));
                    RedisSetup();

                    Console.WriteLine("Restart successful"); 
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[RestartLogic]: Failed due to... {ex}");
            }
            await Task.Delay(200);
        }

        public async Task RefreshLogic()
        {
            string refreshString = RedisManager.GetString(mptRefresh);
            string startStateString = RedisManager.GetString($"{mptStart}_state");
            bool refreshBoolSuccess = bool.TryParse(refreshString, out bool refreshBool);
            bool startStateBoolSuccess = bool.TryParse(startStateString, out bool startStateBool);

            try
            {
                Console.WriteLine($"Refresh Bool fulfilled: {refreshBool}\tstartStateBool fulfilled: {startStateBool}");

                if (refreshBool && startStateBool)
                {
                    SaveSpectrumUIHelper.StopMonitoringMeasurement();
                    await Task.Delay(2000);
                    SaveSpectrumUIHelper.StartMonitoringMeasurement();

                    Console.WriteLine("Refresh sucessful");  

                    RedisManager.SetString($"{mptRefresh}_state", Convert.ToString(refreshBool));
                    RedisManager.SetString($"{mptStart}_state", Convert.ToString(!refreshBool));
                    RedisManager.SetString($"{mptStop}_state", Convert.ToString(refreshBool));
                    RedisManager.SetString($"{mptRefresh}", Convert.ToString(!refreshBool));
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[RefreshLogic]: Failed due to... {ex}");
            }

            await Task.Delay(200);
        }
        public async Task StartLogic()
        {
            string startString = RedisManager.GetString(mptStart);
            string stopStateString = RedisManager.GetString($"{mptStop}_state");
            bool startBoolSuccess = bool.TryParse(startString, out bool startBool);
            bool stopStateBoolSuccess = bool.TryParse(stopStateString, out bool stopStateBool);

            try
            {
                Console.WriteLine($"Start Bool fulfilled: {startBool}\tstopStateBool fulfilled: {stopStateBool}");

                if (startBool && stopStateBool)
                {
                    SaveSpectrumUIHelper.StartMonitoringMeasurement();

                    Console.WriteLine("StartMonitor Measurement sucessful"); 

                    RedisManager.SetString($"{mptStart}_state", Convert.ToString(startBool));
                    RedisManager.SetString($"{mptStop}_state", Convert.ToString(!startBool));
                    RedisManager.SetString($"{mptStart}", Convert.ToString(!startBool));
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[StartLogic]: Failed due to... {ex}");
            }
            await Task.Delay(200);
        }

        public async Task StopLogic()
        {
            string stopString = RedisManager.GetString(mptStop);
            string startStateString = RedisManager.GetString($"{mptStart}_state");
            bool stopBoolSuccess = bool.TryParse(stopString, out bool stopBool);
            bool startStateBoolSuccess = bool.TryParse(startStateString, out bool startStateBool);

            try
            {
                Console.WriteLine($"Stop Bool fulfilled: {stopBool}\tstartStateBool fulfilled: {startStateBool}");

                if (stopBool && startStateBool)
                {
                    SaveSpectrumUIHelper.StopMonitoringMeasurement();
                    Console.WriteLine($"Stop monitoring and measurement sucessful"); 

                    RedisManager.SetString($"{mptStart}_state", Convert.ToString(!stopBool));
                    RedisManager.SetString($"{mptStop}_state", Convert.ToString(stopBool));
                    RedisManager.SetString($"{mptStop}", Convert.ToString(!stopBool));
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[StopLogic]: Failed due to... {ex}");
            }
            await Task.Delay(200);
        }
    }
}
