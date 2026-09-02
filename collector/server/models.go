package server

import "time"

type TrackEventRequest struct {
	TS           string `json:"ts"`
	EventID      string `json:"event_id"`
	ProjectToken string `json:"project_token"`
	UserID       int64  `json:"user_id"`
	ChatID       int64  `json:"chat_id"`
	Handler      string `json:"handler"`
	UpdateType   string `json:"update_type"`
	Payload      string `json:"payload"`
}

type TrackTrafficRequest struct {
	TS           string `json:"ts"`
	ProjectToken string `json:"project_token"`
	UserID       int64  `json:"user_id"`
	StartPayload string `json:"start_payload"`
	UTMSource    string `json:"utm_source"`
	UTMCampaign  string `json:"utm_campaign"`
	Referrer     string `json:"referrer"`
}

type TrackErrorRequest struct {
	TS           string `json:"ts"`
	ProjectToken string `json:"project_token"`
	UserID       int64  `json:"user_id"`
	ErrorType    string `json:"error_type"`
	ErrorMessage string `json:"error_message"`
	Stack        string `json:"stack"`
}

type TrackPurchaseRequest struct {
	TS              string  `json:"ts"`
	ProjectToken    string  `json:"project_token"`
	UserID          int64   `json:"user_id"`
	Amount          float64 `json:"amount"`
	Currency        string  `json:"currency"`
	ProductID       string  `json:"product_id"`
	PaymentProvider string  `json:"payment_provider"`
}

func ParseTime(ts string, layout string) time.Time {
	t, err := time.Parse(layout, ts)
	if err != nil {
		return time.Now().UTC()
	}
	return t
}
