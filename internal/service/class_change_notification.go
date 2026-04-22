package service

import (
	"context"
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

type CancelledClassRepository interface {
	ListUpcoming(ctx context.Context, from time.Time) ([]domain.CancelledClass, error)
}

type MakeupClassRepository interface {
	ListUpcoming(ctx context.Context, from time.Time) ([]domain.MakeupClass, error)
}

type RoomChangeRepository interface {
	ListUpcoming(ctx context.Context, from time.Time) ([]domain.RoomChange, error)
}

type CourseRegistrationRepository interface {
	ListUserIDsBySubject(ctx context.Context, subjectID string) ([]string, error)
}

type NotificationRepository interface {
	UpsertNotification(ctx context.Context, notification domain.Notification) (domain.Notification, error)
}

type ClassChangeNotificationService struct {
	cancelled    CancelledClassRepository
	makeup       MakeupClassRepository
	roomChange   RoomChangeRepository
	courseReg    CourseRegistrationRepository
	notification NotificationRepository
}

func NewClassChangeNotificationService(
	cancelled CancelledClassRepository,
	makeup MakeupClassRepository,
	roomChange RoomChangeRepository,
	courseReg CourseRegistrationRepository,
	notification NotificationRepository,
) *ClassChangeNotificationService {
	return &ClassChangeNotificationService{
		cancelled:    cancelled,
		makeup:       makeup,
		roomChange:   roomChange,
		courseReg:    courseReg,
		notification: notification,
	}
}
