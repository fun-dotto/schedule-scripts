package service

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/domain"
	"github.com/google/uuid"
)

type EnqueueSummary struct {
	CancelledEnqueued  int
	MakeupEnqueued     int
	RoomChangeEnqueued int
	Skipped            int
}

var jst = time.FixedZone("JST", 9*3600)

func (s *ClassChangeNotificationService) EnqueueNotifications(ctx context.Context) (EnqueueSummary, error) {
	var summary EnqueueSummary

	today := time.Now().In(jst)
	todayStart := time.Date(today.Year(), today.Month(), today.Day(), 0, 0, 0, 0, jst)

	cancelled, err := s.cancelled.ListUpcoming(ctx, todayStart)
	if err != nil {
		return summary, fmt.Errorf("list cancelled_classes: %w", err)
	}
	for _, cc := range cancelled {
		enqueued, err := s.enqueueOne(ctx, notificationSpec{
			sourceType: "cancelled",
			sourceID:   cc.ID,
			subjectID:  cc.Subject.ID,
			title:      "休講のお知らせ",
			message:    fmt.Sprintf("明日、%sの%sは休講です。", periodJa(cc.Period), cc.Subject.Name),
			classDate:  cc.Date,
		})
		if err != nil {
			return summary, fmt.Errorf("enqueue cancelled %s: %w", cc.ID, err)
		}
		if enqueued {
			summary.CancelledEnqueued++
		} else {
			summary.Skipped++
		}
	}

	makeup, err := s.makeup.ListUpcoming(ctx, todayStart)
	if err != nil {
		return summary, fmt.Errorf("list makeup_classes: %w", err)
	}
	for _, m := range makeup {
		enqueued, err := s.enqueueOne(ctx, notificationSpec{
			sourceType: "makeup",
			sourceID:   m.ID,
			subjectID:  m.Subject.ID,
			title:      "補講のお知らせ",
			message:    fmt.Sprintf("明日、%sに%sの補講があります。", periodJa(m.Period), m.Subject.Name),
			classDate:  m.Date,
		})
		if err != nil {
			return summary, fmt.Errorf("enqueue makeup %s: %w", m.ID, err)
		}
		if enqueued {
			summary.MakeupEnqueued++
		} else {
			summary.Skipped++
		}
	}

	roomChange, err := s.roomChange.ListUpcoming(ctx, todayStart)
	if err != nil {
		return summary, fmt.Errorf("list room_changes: %w", err)
	}
	for _, rc := range roomChange {
		enqueued, err := s.enqueueOne(ctx, notificationSpec{
			sourceType: "room_change",
			sourceID:   rc.ID,
			subjectID:  rc.Subject.ID,
			title:      "教室変更のお知らせ",
			message:    fmt.Sprintf("明日、%sの%sの教室が%sに変更されます。", periodJa(rc.Period), rc.Subject.Name, rc.NewRoom.Name),
			classDate:  rc.Date,
		})
		if err != nil {
			return summary, fmt.Errorf("enqueue room_change %s: %w", rc.ID, err)
		}
		if enqueued {
			summary.RoomChangeEnqueued++
		} else {
			summary.Skipped++
		}
	}

	return summary, nil
}

type notificationSpec struct {
	sourceType string
	sourceID   string
	subjectID  string
	title      string
	message    string
	classDate  time.Time
}

func (s *ClassChangeNotificationService) enqueueOne(ctx context.Context, spec notificationSpec) (bool, error) {
	userIDs, err := s.courseReg.ListUserIDsBySubject(ctx, spec.subjectID)
	if err != nil {
		return false, fmt.Errorf("list user_ids for subject %s: %w", spec.subjectID, err)
	}
	if len(userIDs) == 0 {
		log.Printf("skip: no enrolled users for %s:%s (subject_id=%s)", spec.sourceType, spec.sourceID, spec.subjectID)
		return false, nil
	}

	notifyAfter, notifyBefore := notifyWindow(spec.classDate)

	n := domain.Notification{
		ID:            deterministicNotificationID(spec.sourceType, spec.sourceID),
		Title:         spec.title,
		Message:       spec.message,
		URL:           nil,
		NotifyAfter:   notifyAfter,
		NotifyBefore:  notifyBefore,
		IsNotified:    false,
		TargetUserIDs: userIDs,
	}
	if _, err := s.notification.UpsertNotification(ctx, n); err != nil {
		return false, err
	}
	return true, nil
}

func deterministicNotificationID(sourceType, sourceID string) string {
	key := fmt.Sprintf("urn:schedule-scripts:class-change:%s:%s", sourceType, sourceID)
	return uuid.NewSHA1(uuid.NameSpaceURL, []byte(key)).String()
}

func notifyWindow(classDate time.Time) (notifyAfter, notifyBefore time.Time) {
	classDayJST := time.Date(classDate.Year(), classDate.Month(), classDate.Day(), 0, 0, 0, 0, jst)
	notifyAfter = classDayJST.AddDate(0, 0, -1).Add(18 * time.Hour)
	notifyBefore = classDayJST
	return
}

func periodJa(p string) string {
	switch p {
	case "Period1":
		return "1限"
	case "Period2":
		return "2限"
	case "Period3":
		return "3限"
	case "Period4":
		return "4限"
	case "Period5":
		return "5限"
	case "Period6":
		return "6限"
	default:
		return p
	}
}
