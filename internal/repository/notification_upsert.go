package repository

import (
	"context"
	"errors"

	"github.com/fun-dotto/schedule-scripts/internal/database"
	"github.com/fun-dotto/schedule-scripts/internal/domain"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

func (r *NotificationRepository) UpsertNotification(ctx context.Context, notification domain.Notification) (domain.Notification, error) {
	if notification.ID == "" {
		return domain.Notification{}, errors.New("notification ID is required for upsert")
	}

	dbNotification := database.NotificationFromDomain(notification)
	uniqueTargets := uniqueTargetUsers(notification.TargetUsers)

	err := r.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		// ID 衝突時は本文を更新しない (再通知・重複配信を防ぐため)。target_users の増減のみ下で同期する。
		if err := tx.Clauses(clause.OnConflict{
			Columns:   []clause.Column{{Name: "id"}},
			DoNothing: true,
		}).Create(&dbNotification).Error; err != nil {
			return err
		}

		if len(uniqueTargets) == 0 {
			return tx.Where("notification_id = ?", notification.ID).
				Delete(&database.NotificationTargetUser{}).Error
		}

		userIDs := make([]string, 0, len(uniqueTargets))
		for _, t := range uniqueTargets {
			userIDs = append(userIDs, t.UserID)
		}
		if err := tx.Where("notification_id = ? AND user_id NOT IN ?", notification.ID, userIDs).
			Delete(&database.NotificationTargetUser{}).Error; err != nil {
			return err
		}

		targets := make([]database.NotificationTargetUser, 0, len(uniqueTargets))
		for _, t := range uniqueTargets {
			targets = append(targets, database.NotificationTargetUser{
				NotificationID: notification.ID,
				UserID:         t.UserID,
				NotifiedAt:     t.NotifiedAt,
			})
		}
		// 既存行は notified_at を保持したいので競合時は何もしない。
		return tx.Clauses(clause.OnConflict{
			Columns:   []clause.Column{{Name: "notification_id"}, {Name: "user_id"}},
			DoNothing: true,
		}).Create(&targets).Error
	})
	if err != nil {
		return domain.Notification{}, err
	}

	return dbNotification.ToDomain(uniqueTargets), nil
}
