using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.ServiceProcess;
using System.Text;
using System.Threading.Tasks;
using StackExchange.Redis;


namespace MPTControlService
{
    public class RedisManager
    {
        private static ConnectionMultiplexer redis;
        private static IDatabase db;

        public static void Init(string connectionString = "localhost")
        {
            redis = ConnectionMultiplexer.Connect(connectionString);
            db = redis.GetDatabase(); 
        }

        public static void SetString(string key, string value)
        {
            db.StringSet(key, value); 
        }

        public static string GetString(string key)
        {
            return db.StringGet(key); 
        }
        public static void Dispose()
        {
            redis.Dispose();
        }

    }
    internal static class Program
    {

        /// <summary>
        /// The main entry point for the application.
        /// </summary>
        static void Main()
        {
            ServiceBase[] ServicesToRun;
            ServicesToRun = new ServiceBase[]
            {
                new MPTControl()
            };
            ServiceBase.Run(ServicesToRun);
        }
    }
}
