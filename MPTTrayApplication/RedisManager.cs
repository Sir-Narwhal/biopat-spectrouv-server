using StackExchange.Redis;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;


namespace MPTTrayApplication
{
    public static class RedisManager
    {
        private static ConnectionMultiplexer redis;
        private static IDatabase db;

        public static void Init(string connectionString = "localhost")
        {
            try
            {
                redis = ConnectionMultiplexer.Connect(connectionString);
                db = redis.GetDatabase();
                Console.WriteLine("Redis connected!");
            }
            catch (ArgumentException ex)
            {
                Console.WriteLine("Invalid Redis config: " + ex.Message);
                throw;
            }
            catch (RedisConnectionException ex)
            {
                Console.WriteLine("Redis connection failed: " + ex.Message);
                throw;
            }
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
}
