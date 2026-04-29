package repository

import (
	"context"
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/database"
)

// MarkUsersAsNotified は通知ID毎に指定ユーザーの notification_target_users.notified_at を現在時刻で更新する。
// 既に notified_at が入っているユーザーは上書きしない。
func (r *NotificationRepository) MarkUsersAsNotified(ctx context.Context, deliveries map[string][]string) error {
	if len(deliveries) == 0 {
		return nil
	}

	now := time.Now()
	for nid, userIDs := range deliveries {
		uniqueUsers := uniqueStrings(userIDs)
		if len(uniqueUsers) == 0 {
			continue
		}
		if err := r.db.WithContext(ctx).
			Model(&database.NotificationTargetUser{}).
			Where("notification_id = ? AND user_id IN ? AND notified_at IS NULL", nid, uniqueUsers).
			Update("notified_at", now).Error; err != nil {
			return err
		}
	}
	return nil
}
