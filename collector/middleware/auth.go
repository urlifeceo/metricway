package middleware

import (
	"github.com/gofiber/fiber/v2"
)

func TokenAuth(validator func(token string) bool) fiber.Handler {
	return func(c *fiber.Ctx) error {
		projectToken := c.Get("X-Project-Token")

		if projectToken == "" {
			return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{"error": "missing project token"})
		}

		if validator != nil && !validator(projectToken) {
			return c.Status(fiber.StatusUnauthorized).JSON(fiber.Map{"error": "invalid project token"})
		}

		return c.Next()
	}
}
