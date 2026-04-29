package database

import (
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

type Notification struct {
	ID string `gorm:"type:text;primaryKey"`

	Title                string  `gorm:"type:text;not null"`
	Body                 string  `gorm:"type:text;not null"`
	ImageURL             *string `gorm:"type:text"`
	AnalyticsLabel       *string `gorm:"type:text"`
	APNsBadge            *int    `gorm:"type:integer"`
	APNsSound            *string `gorm:"type:text"`
	APNsContentAvailable *bool   `gorm:"type:boolean"`
	AndroidChannelID     *string `gorm:"type:text"`
	AndroidPriority      *string `gorm:"type:text"`
	AndroidTTLSeconds    *int    `gorm:"type:integer"`
	WebpushLink          *string `gorm:"type:text"`

	URL *string `gorm:"type:text"`

	NotifyAfter  time.Time `gorm:"type:timestamptz;not null;index"`
	NotifyBefore time.Time `gorm:"type:timestamptz;not null;index"`
}

func (n *Notification) ToDomain(targetUsers []domain.NotificationTargetUser) domain.Notification {
	return domain.Notification{
		ID:                   n.ID,
		Title:                n.Title,
		Body:                 n.Body,
		ImageURL:             n.ImageURL,
		AnalyticsLabel:       n.AnalyticsLabel,
		APNsBadge:            n.APNsBadge,
		APNsSound:            n.APNsSound,
		APNsContentAvailable: n.APNsContentAvailable,
		AndroidChannelID:     n.AndroidChannelID,
		AndroidPriority:      n.AndroidPriority,
		AndroidTTLSeconds:    n.AndroidTTLSeconds,
		WebpushLink:          n.WebpushLink,
		URL:                  n.URL,
		NotifyAfter:          n.NotifyAfter,
		NotifyBefore:         n.NotifyBefore,
		TargetUsers:          targetUsers,
	}
}

func NotificationFromDomain(n domain.Notification) Notification {
	return Notification{
		ID:                   n.ID,
		Title:                n.Title,
		Body:                 n.Body,
		ImageURL:             n.ImageURL,
		AnalyticsLabel:       n.AnalyticsLabel,
		APNsBadge:            n.APNsBadge,
		APNsSound:            n.APNsSound,
		APNsContentAvailable: n.APNsContentAvailable,
		AndroidChannelID:     n.AndroidChannelID,
		AndroidPriority:      n.AndroidPriority,
		AndroidTTLSeconds:    n.AndroidTTLSeconds,
		WebpushLink:          n.WebpushLink,
		URL:                  n.URL,
		NotifyAfter:          n.NotifyAfter,
		NotifyBefore:         n.NotifyBefore,
	}
}
