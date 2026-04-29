package repository

import "github.com/fun-dotto/schedule-scripts/internal/domain"

func uniqueStrings(s []string) []string {
	seen := make(map[string]struct{}, len(s))
	result := make([]string, 0, len(s))
	for _, v := range s {
		if _, ok := seen[v]; ok {
			continue
		}
		seen[v] = struct{}{}
		result = append(result, v)
	}
	return result
}

func uniqueTargetUsers(targets []domain.NotificationTargetUser) []domain.NotificationTargetUser {
	seen := make(map[string]struct{}, len(targets))
	result := make([]domain.NotificationTargetUser, 0, len(targets))
	for _, t := range targets {
		if _, ok := seen[t.UserID]; ok {
			continue
		}
		seen[t.UserID] = struct{}{}
		result = append(result, t)
	}
	return result
}
