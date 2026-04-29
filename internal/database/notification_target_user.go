package database

import "time"

type NotificationTargetUser struct {
	NotificationID string     `gorm:"type:text;primaryKey"`
	UserID         string     `gorm:"type:text;primaryKey"`
	NotifiedAt     *time.Time `gorm:"type:timestamptz;index"`
}
