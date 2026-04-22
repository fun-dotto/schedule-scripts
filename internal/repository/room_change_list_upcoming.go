package repository

import (
	"context"
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/database"
	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

func (r *RoomChangeRepository) ListUpcoming(ctx context.Context, after time.Time) ([]domain.RoomChange, error) {
	var rows []database.RoomChange
	if err := r.db.WithContext(ctx).
		Preload("Subject").
		Preload("NewRoom").
		Where("date > ?", after).
		Find(&rows).Error; err != nil {
		return nil, err
	}
	out := make([]domain.RoomChange, 0, len(rows))
	for i := range rows {
		out = append(out, rows[i].ToDomain())
	}
	return out, nil
}
