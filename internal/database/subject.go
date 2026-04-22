package database

import "github.com/fun-dotto/schedule-scripts/internal/domain"

type Subject struct {
	ID   string `gorm:"type:uuid;primaryKey"`
	Name string `gorm:"not null"`
}

func (m *Subject) ToDomain() domain.Subject {
	return domain.Subject{
		ID:   m.ID,
		Name: m.Name,
	}
}
