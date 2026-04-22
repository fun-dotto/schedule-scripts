package repository

import (
	"context"

	"github.com/fun-dotto/schedule-scripts/internal/database"
)

func (r *NotificationRepository) MarkAsDispatched(ctx context.Context, ids []string) error {
	uniqueIDs := uniqueStrings(ids)
	if len(uniqueIDs) == 0 {
		return nil
	}
	return r.db.WithContext(ctx).Model(&database.Notification{}).
		Where("id IN ?", uniqueIDs).
		Update("is_notified", true).Error
}
