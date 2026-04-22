package service

import (
	"context"

	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

type NotificationRepository interface {
	CreateNotification(ctx context.Context, notification domain.Notification) (domain.Notification, error)
}

type NotificationService struct {
	repo NotificationRepository
}

func NewNotificationService(repo NotificationRepository) *NotificationService {
	return &NotificationService{repo: repo}
}
