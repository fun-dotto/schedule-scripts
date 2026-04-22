package database

import (
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

type FCMToken struct {
	Token     string    `gorm:"type:text;primaryKey"`
	UserID    string    `gorm:"column:user_id;type:text;not null;index"`
	CreatedAt time.Time `gorm:"type:timestamptz;not null"`
	UpdatedAt time.Time `gorm:"type:timestamptz;not null;index"`
}

func (t *FCMToken) ToDomain() domain.FCMToken {
	return domain.FCMToken{
		Token:     t.Token,
		UserID:    t.UserID,
		CreatedAt: t.CreatedAt,
		UpdatedAt: t.UpdatedAt,
	}
}
