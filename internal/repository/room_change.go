package repository

import "gorm.io/gorm"

type RoomChangeRepository struct {
	db *gorm.DB
}

func NewRoomChangeRepository(db *gorm.DB) *RoomChangeRepository {
	return &RoomChangeRepository{db: db}
}
