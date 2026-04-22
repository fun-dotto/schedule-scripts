package database

import (
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

type Notification struct {
	ID         string    `gorm:"type:text;primaryKey"`
	Title      string    `gorm:"type:text;not null"`
	Message    string    `gorm:"type:text;not null"`
	URL        *string   `gorm:"type:text"`
	NotifyAt   time.Time `gorm:"type:timestamptz;not null;index"`
	IsNotified bool      `gorm:"type:boolean;not null;default:false;index"`
}

func (n *Notification) ToDomain(targetUserIDs []string) domain.Notification {
	return domain.Notification{
		ID:            n.ID,
		Title:         n.Title,
		Message:       n.Message,
		URL:           n.URL,
		NotifyAt:      n.NotifyAt,
		IsNotified:    n.IsNotified,
		TargetUserIDs: targetUserIDs,
	}
}

func NotificationFromDomain(n domain.Notification) Notification {
	return Notification{
		ID:         n.ID,
		Title:      n.Title,
		Message:    n.Message,
		URL:        n.URL,
		NotifyAt:   n.NotifyAt,
		IsNotified: n.IsNotified,
	}
}
