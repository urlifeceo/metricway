package config

import (
	"os"
	"strconv"
	"time"
)

type Config struct {
	HTTPPort        string
	CHAddr          string
	CHDatabase      string
	CHUser          string
	CHPassword      string
	BatchSize       int
	FlushInterval   time.Duration
	CollectorSecret string
}

func Load() *Config {
	return &Config{
		HTTPPort:        getEnv("HTTP_PORT", ":8080"),
		CHAddr:          getEnv("CLICKHOUSE_ADDR", "127.0.0.1:9000"),
		CHDatabase:      getEnv("CLICKHOUSE_DB", "tgmetrics"),
		CHUser:          getEnv("CLICKHOUSE_USER", "default"),
		CHPassword:      getEnv("CLICKHOUSE_PASSWORD", ""),
		BatchSize:       getEnvInt("BATCH_SIZE", 1000),
		FlushInterval:   time.Duration(getEnvInt("FLUSH_INTERVAL_SEC", 2)) * time.Second,
		CollectorSecret: getEnv("COLLECTOR_SECRET", ""),
	}
}

func getEnv(key, fallback string) string {
	if val, ok := os.LookupEnv(key); ok {
		return val
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	if val, ok := os.LookupEnv(key); ok {
		if i, err := strconv.Atoi(val); err == nil {
			return i
		}
	}
	return fallback
}
