package repository

import "gorm.io/gorm"

type MakeupClassRepository struct {
	db *gorm.DB
}

func NewMakeupClassRepository(db *gorm.DB) *MakeupClassRepository {
	return &MakeupClassRepository{db: db}
}
