package repository

import (
	"context"
	"time"

	"github.com/fun-dotto/schedule-scripts/internal/database"
	"github.com/fun-dotto/schedule-scripts/internal/domain"
)

func (r *MakeupClassRepository) ListByDate(ctx context.Context, date time.Time) ([]domain.MakeupClass, error) {
	var rows []database.MakeupClass
	if err := r.db.WithContext(ctx).
		Preload("Subject").
		Where("date = ?", date.Format("2006-01-02")).
		Find(&rows).Error; err != nil {
		return nil, err
	}
	out := make([]domain.MakeupClass, 0, len(rows))
	for i := range rows {
		out = append(out, rows[i].ToDomain())
	}
	return out, nil
}
