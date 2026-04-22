package service

import (
	"context"

	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

func (s *NotificationService) CreateNotification(ctx context.Context, notification domain.Notification) (domain.Notification, error) {
	return s.repo.CreateNotification(ctx, notification)
}
