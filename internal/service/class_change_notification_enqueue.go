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
	tomorrow := time.Date(today.Year(), today.Month(), today.Day(), 0, 0, 0, 0, jst).AddDate(0, 0, 1)

	cancelled, err := s.cancelled.ListByDate(ctx, tomorrow)
	if err != nil {
		return summary, fmt.Errorf("list cancelled_classes: %w", err)
	}
	for _, cc := range cancelled {
		var body string
		if periodStr, ok := periodJa(cc.Period); ok {
			body = fmt.Sprintf("明日、%sの%sは休講です。", periodStr, cc.Subject.Name)
		} else {
			log.Printf("warn: unknown period %q for cancelled %s", cc.Period, cc.ID)
			body = fmt.Sprintf("明日、%sが休講です。", cc.Subject.Name)
		}
		enqueued, err := s.enqueueOne(ctx, notificationSpec{
			sourceType: "cancelled",
			sourceID:   cc.ID,
			subjectID:  cc.Subject.ID,
			title:      "休講のお知らせ",
			body:       body,
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

	makeup, err := s.makeup.ListByDate(ctx, tomorrow)
	if err != nil {
		return summary, fmt.Errorf("list makeup_classes: %w", err)
	}
	for _, m := range makeup {
		var body string
		if periodStr, ok := periodJa(m.Period); ok {
			body = fmt.Sprintf("明日、%sに%sの補講があります。", periodStr, m.Subject.Name)
		} else {
			log.Printf("warn: unknown period %q for makeup %s", m.Period, m.ID)
			body = fmt.Sprintf("明日、%sの補講があります。", m.Subject.Name)
		}
		enqueued, err := s.enqueueOne(ctx, notificationSpec{
			sourceType: "makeup",
			sourceID:   m.ID,
			subjectID:  m.Subject.ID,
			title:      "補講のお知らせ",
			body:       body,
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

	roomChange, err := s.roomChange.ListByDate(ctx, tomorrow)
	if err != nil {
		return summary, fmt.Errorf("list room_changes: %w", err)
	}
	for _, rc := range roomChange {
		var body string
		if periodStr, ok := periodJa(rc.Period); ok {
			body = fmt.Sprintf("明日、%sの%sの教室が%sに変更されます。", periodStr, rc.Subject.Name, rc.NewRoom.Name)
		} else {
			log.Printf("warn: unknown period %q for room_change %s", rc.Period, rc.ID)
			body = fmt.Sprintf("明日、%sの教室が%sに変更されます。", rc.Subject.Name, rc.NewRoom.Name)
		}
		enqueued, err := s.enqueueOne(ctx, notificationSpec{
			sourceType: "room_change",
			sourceID:   rc.ID,
			subjectID:  rc.Subject.ID,
			title:      "教室変更のお知らせ",
			body:       body,
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
	body       string
	classDate  time.Time
}

// APNsSound はクライアント側でデフォルト通知音を鳴らすために "default" を指定する。
var defaultAPNsSound = "default"

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

	targetUsers := make([]domain.NotificationTargetUser, 0, len(userIDs))
	for _, uid := range userIDs {
		targetUsers = append(targetUsers, domain.NotificationTargetUser{UserID: uid})
	}

	n := domain.Notification{
		ID:           deterministicNotificationID(spec.sourceType, spec.sourceID),
		Title:        spec.title,
		Body:         spec.body,
		APNsSound:    &defaultAPNsSound,
		URL:          nil,
		NotifyAfter:  notifyAfter,
		NotifyBefore: notifyBefore,
		TargetUsers:  targetUsers,
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

func periodJa(p string) (string, bool) {
	switch p {
	case "Period1":
		return "1限", true
	case "Period2":
		return "2限", true
	case "Period3":
		return "3限", true
	case "Period4":
		return "4限", true
	case "Period5":
		return "5限", true
	case "Period6":
		return "6限", true
	default:
		return "", false
	}
}
