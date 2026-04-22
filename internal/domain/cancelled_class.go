package domain

import "time"

type CancelledClass struct {
	ID      string
	Subject Subject
	Date    time.Time
	Period  string
}
