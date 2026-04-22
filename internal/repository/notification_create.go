package repository

import (
	"context"

	"github.com/fun-dotto/schedule-scripts/internal/database"
	"github.com/fun-dotto/schedule-scripts/internal/domain"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

func (r *NotificationRepository) CreateNotification(ctx context.Context, notification domain.Notification) (domain.Notification, error) {
	notification.ID = uuid.New().String()

	dbNotification := database.NotificationFromDomain(notification)

	err := r.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if err := tx.Create(&dbNotification).Error; err != nil {
			return err
		}

		uniqueIDs := uniqueStrings(notification.TargetUserIDs)
		if len(uniqueIDs) > 0 {
			targets := make([]database.NotificationTargetUser, 0, len(uniqueIDs))
			for _, userID := range uniqueIDs {
				targets = append(targets, database.NotificationTargetUser{
					NotificationID: notification.ID,
					UserID:         userID,
				})
			}
			if err := tx.Create(&targets).Error; err != nil {
				return err
			}
		}

		return nil
	})
	if err != nil {
		return domain.Notification{}, err
	}

	return dbNotification.ToDomain(uniqueStrings(notification.TargetUserIDs)), nil
}
