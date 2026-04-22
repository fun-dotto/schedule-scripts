package database

import (
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

type CancelledClass struct {
	ID        string    `gorm:"type:uuid;primaryKey"`
	SubjectID string    `gorm:"type:uuid;not null"`
	Subject   *Subject  `gorm:"foreignKey:SubjectID"`
	Date      time.Time `gorm:"type:date;not null"`
	Period    string    `gorm:"not null"`
}

func (m *CancelledClass) ToDomain() domain.CancelledClass {
	d := domain.CancelledClass{
		ID:     m.ID,
		Date:   m.Date,
		Period: m.Period,
	}
	if m.Subject != nil {
		d.Subject = m.Subject.ToDomain()
	}
	return d
}
