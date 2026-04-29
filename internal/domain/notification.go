package domain

import "time"

type Notification struct {
	ID string

	Title                string
	Body                 string
	ImageURL             *string
	AnalyticsLabel       *string
	APNsBadge            *int
	APNsSound            *string
	APNsContentAvailable *bool
	AndroidChannelID     *string
	AndroidPriority      *string
	AndroidTTLSeconds    *int
	WebpushLink          *string

	URL *string

	NotifyAfter  time.Time
	NotifyBefore time.Time

	TargetUsers []NotificationTargetUser
}

type NotificationTargetUser struct {
	UserID     string
	NotifiedAt *time.Time
}
