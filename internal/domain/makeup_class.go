package domain

import "time"

type MakeupClass struct {
	ID      string
	Subject Subject
	Date    time.Time
	Period  string
}
