package database

type CourseRegistration struct {
	ID        string `gorm:"type:uuid;primaryKey"`
	UserID    string `gorm:"not null"`
	SubjectID string `gorm:"type:uuid;not null"`
}
