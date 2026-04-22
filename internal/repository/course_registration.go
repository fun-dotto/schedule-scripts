package repository

import "gorm.io/gorm"

type CourseRegistrationRepository struct {
	db *gorm.DB
}

func NewCourseRegistrationRepository(db *gorm.DB) *CourseRegistrationRepository {
	return &CourseRegistrationRepository{db: db}
}
