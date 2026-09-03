using MPTSaveSpectrumLibrary;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace MPTControlService
{
    public class MPTLogic
    {
        public string mptStop = "mpt_stop";
        public string mptRefresh = "mpt_refresh";
        public string mptRestart = "mpt-restart";
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
            bool restartBool = bool.TryParse(restartString, out _);

            try
            {

                if (restartBool)
                {
                    SaveSpectrumUIHelper.RestartProgram();
                    SaveSpectrumUIHelper.StartConnectMonitor();
                    RedisManager.SetString($"{mptRestart}_state", Convert.ToString(restartBool));

                    RedisSetup();
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
            bool refreshBool = bool.TryParse(refreshString, out _);
            bool startStateBool = bool.TryParse(startStateString, out _);

            try
            {
                if (refreshBool && startStateBool)
                {
                    SaveSpectrumUIHelper.StopMonitoringMeasurement();
                    await Task.Delay(2000);
                    SaveSpectrumUIHelper.StartMonitoringMeasurement();

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
            bool startBool = bool.TryParse(startString, out _);
            bool stopStateBool = bool.TryParse(stopStateString, out _);

            try
            {
                if (startBool && stopStateBool)
                {
                    SaveSpectrumUIHelper.StartMonitoringMeasurement();

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
            bool stopBool = bool.TryParse(stopString, out _);
            bool startStateBool = bool.TryParse(startStateString, out _);

            try
            {
                if (stopBool && startStateBool)
                {
                    SaveSpectrumUIHelper.StopMonitoringMeasurement();

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
