package domain

import "time"

type Notification struct {
	ID            string
	Title         string
	Message       string
	URL           *string
	NotifyAt      time.Time
	IsNotified    bool
	TargetUserIDs []string
}
