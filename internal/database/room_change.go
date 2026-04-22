package database

import (
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

type RoomChange struct {
	ID             string    `gorm:"type:uuid;primaryKey"`
	SubjectID      string    `gorm:"type:uuid;not null"`
	Subject        *Subject  `gorm:"foreignKey:SubjectID"`
	Date           time.Time `gorm:"type:date;not null"`
	Period         string    `gorm:"not null"`
	OriginalRoomID string    `gorm:"type:uuid;not null"`
	NewRoomID      string    `gorm:"type:uuid;not null"`
	NewRoom        *Room     `gorm:"foreignKey:NewRoomID"`
}

func (m *RoomChange) ToDomain() domain.RoomChange {
	d := domain.RoomChange{
		ID:     m.ID,
		Date:   m.Date,
		Period: m.Period,
	}
	if m.Subject != nil {
		d.Subject = m.Subject.ToDomain()
	}
	if m.NewRoom != nil {
		d.NewRoom = m.NewRoom.ToDomain()
	}
	return d
}
