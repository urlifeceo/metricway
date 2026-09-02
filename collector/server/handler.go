package server

import (
	"collector/storage"

	"github.com/gofiber/fiber/v2"
)

type Handler struct {
	collector *storage.Collector
}

func NewHandler(collector *storage.Collector) *Handler {
	return &Handler{collector: collector}
}

func (h *Handler) RegisterRoutes(router fiber.Router) {
	api := router.Group("/track")

	api.Post("/events", h.TrackEvents)
	api.Post("/traffic", h.TrackTraffic)
	api.Post("/errors", h.TrackErrors)
	api.Post("/purchases", h.TrackPurchases)
}

func (h *Handler) TrackEvents(c *fiber.Ctx) error {
	token := c.Get("X-Project-Token")
	if token == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Missing X-Project-Token"})
	}

	var reqs []TrackEventRequest
	if err := c.BodyParser(&reqs); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid payload"})
	}

	events := make([]storage.Event, 0, len(reqs))
	for _, req := range reqs {
		events = append(events, storage.Event{
			TS:           ParseTime(req.TS, "2006-01-02 15:04:05.000"),
			EventID:      req.EventID,
			ProjectToken: token,
			UserID:       req.UserID,
			ChatID:       req.ChatID,
			Handler:      req.Handler,
			UpdateType:   req.UpdateType,
			Payload:      req.Payload,
		})
	}

	h.collector.PushEvents(events)
	return c.Status(fiber.StatusAccepted).JSON(fiber.Map{"status": "queued"})
}

func (h *Handler) TrackTraffic(c *fiber.Ctx) error {
	token := c.Get("X-Project-Token")
	if token == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Missing X-Project-Token"})
	}

	var reqs []TrackTrafficRequest
	if err := c.BodyParser(&reqs); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid payload"})
	}

	traffic := make([]storage.Traffic, 0, len(reqs))
	for _, req := range reqs {
		traffic = append(traffic, storage.Traffic{
			TS:           ParseTime(req.TS, "2006-01-02 15:04:05"),
			ProjectToken: token,
			UserID:       req.UserID,
			StartPayload: req.StartPayload,
			UTMSource:    req.UTMSource,
			UTMCampaign:  req.UTMCampaign,
			Referrer:     req.Referrer,
		})
	}

	h.collector.PushTraffic(traffic)
	return c.Status(fiber.StatusAccepted).JSON(fiber.Map{"status": "queued"})
}

func (h *Handler) TrackErrors(c *fiber.Ctx) error {
	token := c.Get("X-Project-Token")
	if token == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Missing X-Project-Token"})
	}

	var reqs []TrackErrorRequest
	if err := c.BodyParser(&reqs); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid payload"})
	}

	errs := make([]storage.ErrorRecord, 0, len(reqs))
	for _, req := range reqs {
		errs = append(errs, storage.ErrorRecord{
			TS:           ParseTime(req.TS, "2006-01-02 15:04:05"),
			ProjectToken: token,
			UserID:       req.UserID,
			ErrorType:    req.ErrorType,
			ErrorMessage: req.ErrorMessage,
			Stack:        req.Stack,
		})
	}

	h.collector.PushErrors(errs)
	return c.Status(fiber.StatusAccepted).JSON(fiber.Map{"status": "queued"})
}

func (h *Handler) TrackPurchases(c *fiber.Ctx) error {
	token := c.Get("X-Project-Token")
	if token == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Missing X-Project-Token"})
	}

	var reqs []TrackPurchaseRequest
	if err := c.BodyParser(&reqs); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "Invalid payload"})
	}

	purchases := make([]storage.Purchase, 0, len(reqs))
	for _, req := range reqs {
		purchases = append(purchases, storage.Purchase{
			TS:              ParseTime(req.TS, "2006-01-02 15:04:05"),
			UserID:          req.UserID,
			ProjectToken:    token,
			Amount:          req.Amount,
			Currency:        req.Currency,
			ProductID:       req.ProductID,
			PaymentProvider: req.PaymentProvider,
		})
	}

	h.collector.PushPurchases(purchases)
	return c.Status(fiber.StatusAccepted).JSON(fiber.Map{"status": "queued"})
}
