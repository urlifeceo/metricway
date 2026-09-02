package storage

import (
	"context"
	"log"
	"sync"
	"time"

	"collector/config"

	"github.com/ClickHouse/clickhouse-go/v2"
	"github.com/ClickHouse/clickhouse-go/v2/lib/driver"
)

type Purchase struct {
	TS              time.Time `ch:"ts"`
	UserID          int64     `ch:"user_id"`
	ProjectToken    string    `ch:"project_token"`
	Amount          float64   `ch:"amount"`
	Currency        string    `ch:"currency"`
	ProductID       string    `ch:"product_id"`
	PaymentProvider string    `ch:"payment_provider"`
}

type Event struct {
	TS           time.Time `ch:"ts"`
	EventID      string    `ch:"event_id"`
	ProjectToken string    `ch:"project_token"`
	UserID       int64     `ch:"user_id"`
	ChatID       int64     `ch:"chat_id"`
	Handler      string    `ch:"handler"`
	UpdateType   string    `ch:"update_type"`
	Payload      string    `ch:"payload"`
}

type Traffic struct {
	TS           time.Time `ch:"ts"`
	ProjectToken string    `ch:"project_token"`
	UserID       int64     `ch:"user_id"`
	StartPayload string    `ch:"start_payload"`
	UTMSource    string    `ch:"utm_source"`
	UTMCampaign  string    `ch:"utm_campaign"`
	Referrer     string    `ch:"referrer"`
}

type ErrorRecord struct {
	TS           time.Time `ch:"ts"`
	ProjectToken string    `ch:"project_token"`
	UserID       int64     `ch:"user_id"`
	ErrorType    string    `ch:"error_type"`
	ErrorMessage string    `ch:"error_message"`
	Stack        string    `ch:"stack"`
}

type Collector struct {
	conn          driver.Conn
	eventChan     chan Event
	trafficChan   chan Traffic
	errorChan     chan ErrorRecord
	purchaseChan  chan Purchase
	batchSize     int
	flushInterval time.Duration
	wg            sync.WaitGroup
	ctx           context.Context
	cancel        context.CancelFunc
}

func NewCollector(cfg *config.Config) (*Collector, error) {
	conn, err := clickhouse.Open(&clickhouse.Options{
		Addr: []string{cfg.CHAddr},
		Auth: clickhouse.Auth{
			Database: cfg.CHDatabase,
			Username: cfg.CHUser,
			Password: cfg.CHPassword,
		},
		DialTimeout: 5 * time.Second,
	})
	if err != nil {
		return nil, err
	}

	ctx, cancel := context.WithCancel(context.Background())

	c := &Collector{
		conn:          conn,
		eventChan:     make(chan Event, 10000),
		trafficChan:   make(chan Traffic, 10000),
		errorChan:     make(chan ErrorRecord, 10000),
		purchaseChan:  make(chan Purchase, 10000),
		batchSize:     cfg.BatchSize,
		flushInterval: cfg.FlushInterval,
		ctx:           ctx,
		cancel:        cancel,
	}

	c.wg.Add(4)
	go c.workerEvents()
	go c.workerTraffic()
	go c.workerErrors()
	go c.workerPurchases()

	return c, nil
}

func (c *Collector) PushEvents(events []Event) {
	for _, e := range events {
		select {
		case c.eventChan <- e:
		default:
			log.Println("Events buffer full, dropping event")
		}
	}
}

func (c *Collector) PushTraffic(traffic []Traffic) {
	for _, t := range traffic {
		select {
		case c.trafficChan <- t:
		default:
			log.Println("Traffic buffer full, dropping traffic record")
		}
	}
}

func (c *Collector) PushErrors(errors []ErrorRecord) {
	for _, e := range errors {
		select {
		case c.errorChan <- e:
		default:
			log.Println("Errors buffer full, dropping error record")
		}
	}
}

func (c *Collector) PushPurchases(purchases []Purchase) {
	for _, p := range purchases {
		select {
		case c.purchaseChan <- p:
		default:
			log.Println("Purchases buffer full, dropping record")
		}
	}
}

func (c *Collector) workerEvents() {
	defer c.wg.Done()
	ticker := time.NewTicker(c.flushInterval)
	defer ticker.Stop()

	var batch []Event

	for {
		select {
		case <-c.ctx.Done():
			c.flushEvents(batch)
			return
		case event := <-c.eventChan:
			batch = append(batch, event)
			if len(batch) >= c.batchSize {
				c.flushEvents(batch)
				batch = make([]Event, 0, c.batchSize)
			}
		case <-ticker.C:
			if len(batch) > 0 {
				c.flushEvents(batch)
				batch = make([]Event, 0, c.batchSize)
			}
		}
	}
}

func (c *Collector) workerTraffic() {
	defer c.wg.Done()
	ticker := time.NewTicker(c.flushInterval)
	defer ticker.Stop()

	var batch []Traffic

	for {
		select {
		case <-c.ctx.Done():
			c.flushTraffic(batch)
			return
		case t := <-c.trafficChan:
			batch = append(batch, t)
			if len(batch) >= c.batchSize {
				c.flushTraffic(batch)
				batch = make([]Traffic, 0, c.batchSize)
			}
		case <-ticker.C:
			if len(batch) > 0 {
				c.flushTraffic(batch)
				batch = make([]Traffic, 0, c.batchSize)
			}
		}
	}
}

func (c *Collector) workerErrors() {
	defer c.wg.Done()
	ticker := time.NewTicker(c.flushInterval)
	defer ticker.Stop()

	var batch []ErrorRecord

	for {
		select {
		case <-c.ctx.Done():
			c.flushErrors(batch)
			return
		case errRec := <-c.errorChan:
			batch = append(batch, errRec)
			if len(batch) >= c.batchSize {
				c.flushErrors(batch)
				batch = make([]ErrorRecord, 0, c.batchSize)
			}
		case <-ticker.C:
			if len(batch) > 0 {
				c.flushErrors(batch)
				batch = make([]ErrorRecord, 0, c.batchSize)
			}
		}
	}
}

func (c *Collector) workerPurchases() {
	defer c.wg.Done()
	ticker := time.NewTicker(c.flushInterval)
	defer ticker.Stop()

	var batch []Purchase

	for {
		select {
		case <-c.ctx.Done():
			c.flushPurchases(batch)
			return
		case p := <-c.purchaseChan:
			batch = append(batch, p)
			if len(batch) >= c.batchSize {
				c.flushPurchases(batch)
				batch = make([]Purchase, 0, c.batchSize)
			}
		case <-ticker.C:
			if len(batch) > 0 {
				c.flushPurchases(batch)
				batch = make([]Purchase, 0, c.batchSize)
			}
		}
	}
}

func (c *Collector) flushEvents(events []Event) {
	if len(events) == 0 {
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	batch, err := c.conn.PrepareBatch(
		ctx,
		"INSERT INTO tgmetrics.events (ts, event_id, project_token, user_id, chat_id, handler, update_type, payload)",
	)
	if err != nil {
		log.Printf("Failed to prepare events batch: %v", err)
		return
	}
	for _, e := range events {
		if err := batch.Append(e.TS, e.EventID, e.ProjectToken, e.UserID, e.ChatID, e.Handler, e.UpdateType, e.Payload); err != nil {
			log.Printf("Failed to append event: %v", err)
			return
		}
	}
	if err := batch.Send(); err != nil {
		log.Printf("Failed to send events batch to ClickHouse: %v", err)
	}
}

func (c *Collector) flushErrors(errors []ErrorRecord) {
	if len(errors) == 0 {
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	batch, err := c.conn.PrepareBatch(
		ctx,
		"INSERT INTO tgmetrics.errors (ts, project_token, user_id, error_type, error_message, stack)",
	)
	if err != nil {
		log.Printf("Failed to prepare errors batch: %v", err)
		return
	}
	for _, e := range errors {
		if err := batch.Append(e.TS, e.ProjectToken, e.UserID, e.ErrorType, e.ErrorMessage, e.Stack); err != nil {
			log.Printf("Failed to append error record: %v", err)
			return
		}
	}
	if err := batch.Send(); err != nil {
		log.Printf("Failed to send errors batch to ClickHouse: %v", err)
	}
}

func (c *Collector) flushTraffic(traffic []Traffic) {
	if len(traffic) == 0 {
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	batch, err := c.conn.PrepareBatch(
		ctx,
		"INSERT INTO tgmetrics.traffic (user_id, project_token, ts, start_payload, utm_source, utm_campaign, referrer)",
	)
	if err != nil {
		log.Printf("Failed to prepare traffic batch: %v", err)
		return
	}
	for _, t := range traffic {
		if err := batch.Append(t.UserID, t.ProjectToken, t.TS, t.StartPayload, t.UTMSource, t.UTMCampaign, t.Referrer); err != nil {
			log.Printf("Failed to append traffic record: %v", err)
			return
		}
	}
	if err := batch.Send(); err != nil {
		log.Printf("Failed to send traffic batch to ClickHouse: %v", err)
	}
}

func (c *Collector) flushPurchases(purchases []Purchase) {
	if len(purchases) == 0 {
		return
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	batch, err := c.conn.PrepareBatch(
		ctx,
		"INSERT INTO tgmetrics.purchases (ts, user_id, project_token, amount, currency, product_id, payment_provider)",
	)
	if err != nil {
		log.Printf("Failed to prepare purchases batch: %v", err)
		return
	}
	for _, p := range purchases {
		if err := batch.Append(p.TS, p.UserID, p.ProjectToken, p.Amount, p.Currency, p.ProductID, p.PaymentProvider); err != nil {
			log.Printf("Failed to append purchase: %v", err)
			return
		}
	}
	if err := batch.Send(); err != nil {
		log.Printf("Failed to send purchases batch to ClickHouse: %v", err)
	}
}

func (c *Collector) Close() {
	c.cancel()
	c.wg.Wait()
	_ = c.conn.Close()
}
