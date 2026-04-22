package repository

import "gorm.io/gorm"

type CancelledClassRepository struct {
	db *gorm.DB
}

func NewCancelledClassRepository(db *gorm.DB) *CancelledClassRepository {
	return &CancelledClassRepository{db: db}
}
