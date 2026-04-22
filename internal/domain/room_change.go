package domain

import "time"

type RoomChange struct {
	ID      string
	Subject Subject
	Date    time.Time
	Period  string
	NewRoom Room
}
