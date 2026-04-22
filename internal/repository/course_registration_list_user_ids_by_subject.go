package repository

import (
	"context"

	"github.com/fun-dotto/schedule-scripts/internal/database"
)

func (r *CourseRegistrationRepository) ListUserIDsBySubject(ctx context.Context, subjectID string) ([]string, error) {
	var userIDs []string
	if err := r.db.WithContext(ctx).
		Model(&database.CourseRegistration{}).
		Where("subject_id = ?", subjectID).
		Distinct("user_id").
		Pluck("user_id", &userIDs).Error; err != nil {
		return nil, err
	}
	return userIDs, nil
}
