package domain

import "time"

type Notification struct {
	ID            string
	Title         string
	Message       string
	URL           *string
	NotifyAfter   time.Time
	NotifyBefore  time.Time
	IsNotified    bool
	TargetUserIDs []string
}
