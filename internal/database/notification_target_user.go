package database

type NotificationTargetUser struct {
	NotificationID string `gorm:"type:text;primaryKey"`
	UserID         string `gorm:"type:text;primaryKey"`
}
