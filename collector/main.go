package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"

	"collector/config"
	"collector/middleware"
	"collector/server"
	"collector/storage"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/recover"
)

func main() {
	cfg := config.Load()

	chCollector, err := storage.NewCollector(cfg)
	if err != nil {
		log.Fatalf("Failed to connect to ClickHouse: %v", err)
	}
	defer chCollector.Close()

	app := fiber.New()

	app.Use(recover.New())

	app.Use(middleware.TokenAuth(func(token string) bool {
		return token != ""
	}))

	h := server.NewHandler(chCollector)

	collector := app.Group("/collector")
	h.RegisterRoutes(collector)

	go func() {
		if err := app.Listen(cfg.HTTPPort); err != nil {
			log.Fatalf("Server error: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down collector...")
	_ = app.Shutdown()
}
