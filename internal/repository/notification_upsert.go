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
	uniqueIDs := uniqueStrings(notification.TargetUserIDs)

	err := r.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if err := tx.Clauses(clause.OnConflict{
			Columns:   []clause.Column{{Name: "id"}},
			DoNothing: true,
		}).Create(&dbNotification).Error; err != nil {
			return err
		}

		if len(uniqueIDs) == 0 {
			return nil
		}
		targets := make([]database.NotificationTargetUser, 0, len(uniqueIDs))
		for _, userID := range uniqueIDs {
			targets = append(targets, database.NotificationTargetUser{
				NotificationID: notification.ID,
				UserID:         userID,
			})
		}
		return tx.Clauses(clause.OnConflict{
			Columns:   []clause.Column{{Name: "notification_id"}, {Name: "user_id"}},
			DoNothing: true,
		}).Create(&targets).Error
	})
	if err != nil {
		return domain.Notification{}, err
	}

	return dbNotification.ToDomain(uniqueIDs), nil
}
