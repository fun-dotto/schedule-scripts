package repository

import (
	"context"
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/database"
	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

func (r *NotificationRepository) ListPendingNotifications(ctx context.Context, now time.Time) ([]domain.Notification, error) {
	var dbNotifications []database.Notification
	if err := r.db.WithContext(ctx).
		Where("notify_after <= ?", now).
		Where("notify_before > ?", now).
		Where(`EXISTS (
			SELECT 1 FROM notification_target_users tu
			WHERE tu.notification_id = notifications.id
			AND tu.notified_at IS NULL
		)`).
		Order("notify_after ASC").
		Find(&dbNotifications).Error; err != nil {
		return nil, err
	}
	if len(dbNotifications) == 0 {
		return []domain.Notification{}, nil
	}

	notificationIDs := make([]string, 0, len(dbNotifications))
	for _, n := range dbNotifications {
		notificationIDs = append(notificationIDs, n.ID)
	}

	// 未通知ユーザーだけを送信対象として返す。
	var allTargets []database.NotificationTargetUser
	if err := r.db.WithContext(ctx).
		Where("notification_id IN ?", notificationIDs).
		Where("notified_at IS NULL").
		Find(&allTargets).Error; err != nil {
		return nil, err
	}

	targetMap := make(map[string][]domain.NotificationTargetUser)
	for _, t := range allTargets {
		targetMap[t.NotificationID] = append(targetMap[t.NotificationID], domain.NotificationTargetUser{
			UserID:     t.UserID,
			NotifiedAt: t.NotifiedAt,
		})
	}

	notifications := make([]domain.Notification, 0, len(dbNotifications))
	for _, n := range dbNotifications {
		notifications = append(notifications, n.ToDomain(targetMap[n.ID]))
	}

	return notifications, nil
}
