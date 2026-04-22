package domain

import "time"

type FCMToken struct {
	Token     string
	UserID    string
	CreatedAt time.Time
	UpdatedAt time.Time
}

type FCMTokenListFilter struct {
	UserIDs       []string
	Tokens        []string
	UpdatedAtFrom *time.Time
	UpdatedAtTo   *time.Time
}
