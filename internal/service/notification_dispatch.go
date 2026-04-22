package service

import (
	"context"
	"fmt"
	"log"
	"time"

	"firebase.google.com/go/v4/messaging"
	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

type DispatchNotificationRepository interface {
	ListPendingNotifications(ctx context.Context, now time.Time) ([]domain.Notification, error)
	MarkAsDispatched(ctx context.Context, ids []string) error
}

type FCMTokenRepository interface {
	ListFCMTokens(ctx context.Context, filter domain.FCMTokenListFilter) ([]domain.FCMToken, error)
}

type MessagingClient interface {
	SendEachForMulticast(ctx context.Context, msg *messaging.MulticastMessage) (*messaging.BatchResponse, error)
}

type NotificationDispatchService struct {
	notification    DispatchNotificationRepository
	fcmToken        FCMTokenRepository
	messagingClient MessagingClient
}

func NewNotificationDispatchService(
	notification DispatchNotificationRepository,
	fcmToken FCMTokenRepository,
	messagingClient MessagingClient,
) *NotificationDispatchService {
	return &NotificationDispatchService{
		notification:    notification,
		fcmToken:        fcmToken,
		messagingClient: messagingClient,
	}
}

type DispatchSummary struct {
	Pending       int
	Dispatched    int
	NoTokenSkip   int
	FailedSend    int
	TotalFCMSent  int
	DryRun        bool
}

const fcmMulticastBatchSize = 500

func (s *NotificationDispatchService) DispatchNotifications(ctx context.Context, dryRun bool) (DispatchSummary, error) {
	summary := DispatchSummary{DryRun: dryRun}

	now := time.Now()
	notifications, err := s.notification.ListPendingNotifications(ctx, now)
	if err != nil {
		return summary, fmt.Errorf("list pending notifications: %w", err)
	}
	summary.Pending = len(notifications)
	if len(notifications) == 0 {
		return summary, nil
	}

	userIDSet := make(map[string]struct{})
	for _, n := range notifications {
		for _, uid := range n.TargetUserIDs {
			userIDSet[uid] = struct{}{}
		}
	}

	tokensByUser := make(map[string][]string)
	if len(userIDSet) > 0 {
		userIDs := make([]string, 0, len(userIDSet))
		for uid := range userIDSet {
			userIDs = append(userIDs, uid)
		}
		tokens, err := s.fcmToken.ListFCMTokens(ctx, domain.FCMTokenListFilter{UserIDs: userIDs})
		if err != nil {
			return summary, fmt.Errorf("list fcm_tokens: %w", err)
		}
		for _, t := range tokens {
			tokensByUser[t.UserID] = append(tokensByUser[t.UserID], t.Token)
		}
	}

	for _, n := range notifications {
		tokens := collectTokens(n.TargetUserIDs, tokensByUser)
		if len(tokens) == 0 {
			log.Printf("skip: no fcm_tokens for notification %s (targets=%d)", n.ID, len(n.TargetUserIDs))
			summary.NoTokenSkip++
			if dryRun {
				continue
			}
			if err := s.notification.MarkAsDispatched(ctx, []string{n.ID}); err != nil {
				return summary, fmt.Errorf("mark as dispatched %s: %w", n.ID, err)
			}
			continue
		}

		if dryRun {
			log.Printf("dry-run: would send notification %s to %d token(s) (targets=%d) title=%q", n.ID, len(tokens), len(n.TargetUserIDs), n.Title)
			summary.TotalFCMSent += len(tokens)
			summary.Dispatched++
			continue
		}

		sent, err := s.sendToTokens(ctx, n, tokens)
		summary.TotalFCMSent += sent
		if err != nil && sent == 0 {
			log.Printf("FCM send failed for notification %s: %v", n.ID, err)
			summary.FailedSend++
			continue
		}
		if err != nil {
			log.Printf("FCM send partial failure for notification %s (sent=%d, tokens=%d): %v — marking as dispatched to avoid duplicate delivery", n.ID, sent, len(tokens), err)
		}
		if sent == 0 {
			continue
		}
		if err := s.notification.MarkAsDispatched(ctx, []string{n.ID}); err != nil {
			return summary, fmt.Errorf("mark as dispatched %s: %w", n.ID, err)
		}
		summary.Dispatched++
	}

	return summary, nil
}

func collectTokens(userIDs []string, tokensByUser map[string][]string) []string {
	seen := make(map[string]struct{})
	tokens := make([]string, 0)
	for _, uid := range userIDs {
		for _, tk := range tokensByUser[uid] {
			if _, ok := seen[tk]; ok {
				continue
			}
			seen[tk] = struct{}{}
			tokens = append(tokens, tk)
		}
	}
	return tokens
}

func (s *NotificationDispatchService) sendToTokens(ctx context.Context, n domain.Notification, tokens []string) (int, error) {
	data := map[string]string{"notification_id": n.ID}
	if n.URL != nil {
		data["url"] = *n.URL
	}

	totalSuccess := 0
	for start := 0; start < len(tokens); start += fcmMulticastBatchSize {
		end := min(start+fcmMulticastBatchSize, len(tokens))
		msg := &messaging.MulticastMessage{
			Tokens: tokens[start:end],
			Notification: &messaging.Notification{
				Title: n.Title,
				Body:  n.Message,
			},
			Data: data,
		}
		resp, err := s.messagingClient.SendEachForMulticast(ctx, msg)
		if err != nil {
			return totalSuccess, err
		}
		totalSuccess += resp.SuccessCount
		if resp.FailureCount > 0 {
			for i, r := range resp.Responses {
				if r.Error != nil {
					log.Printf("FCM delivery failed for notification %s token=%s: %v", n.ID, redactToken(tokens[start+i]), r.Error)
				}
			}
		}
	}
	return totalSuccess, nil
}

// redactToken は FCM トークンをログ出力する際に、先頭と末尾の数文字だけ残して個人識別につながる情報量を削る。
func redactToken(token string) string {
	const keep = 4
	if len(token) <= keep*2 {
		return "***"
	}
	return token[:keep] + "..." + token[len(token)-keep:]
}
