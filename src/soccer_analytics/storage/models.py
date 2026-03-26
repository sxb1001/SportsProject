from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LeagueModel(Base):
    __tablename__ = "leagues"
    provider_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(100))


class SeasonModel(Base):
    __tablename__ = "seasons"
    provider_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    league_code: Mapped[str] = mapped_column(String(20), ForeignKey("leagues.code"))
    year: Mapped[int] = mapped_column(Integer, index=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)


class TeamModel(Base):
    __tablename__ = "teams"
    provider_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    league_code: Mapped[str] = mapped_column(String(20), index=True)
    season_year: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    short_name: Mapped[str] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(100))


class PlayerModel(Base):
    __tablename__ = "players"
    provider_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    team_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("teams.provider_id"))
    name: Mapped[str] = mapped_column(String(255), index=True)
    position: Mapped[str] = mapped_column(String(20))
    nationality: Mapped[str] = mapped_column(String(100))


class MatchModel(Base):
    __tablename__ = "matches"
    provider_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    league_code: Mapped[str] = mapped_column(String(20), index=True)
    season_year: Mapped[int] = mapped_column(Integer, index=True)
    match_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(50))
    home_team_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("teams.provider_id"))
    away_team_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("teams.provider_id"))
    home_score: Mapped[int] = mapped_column(Integer)
    away_score: Mapped[int] = mapped_column(Integer)


class MatchStatModel(Base):
    __tablename__ = "match_stats"
    match_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("matches.provider_id"), primary_key=True)
    team_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("teams.provider_id"), primary_key=True)
    possession_pct: Mapped[float] = mapped_column(Float)
    shots: Mapped[int] = mapped_column(Integer)
    shots_on_target: Mapped[int] = mapped_column(Integer)
    expected_goals: Mapped[float] = mapped_column(Float)


class PlayerMatchStatModel(Base):
    __tablename__ = "player_match_stats"
    match_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("matches.provider_id"), primary_key=True)
    player_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("players.provider_id"), primary_key=True)
    team_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("teams.provider_id"))
    minutes_played: Mapped[int] = mapped_column(Integer)
    goals: Mapped[int] = mapped_column(Integer)
    assists: Mapped[int] = mapped_column(Integer)
    rating: Mapped[float] = mapped_column(Float)
    passes_completed: Mapped[int] = mapped_column(Integer)


class PlayerHeatmapCellModel(Base):
    __tablename__ = "player_heatmap_cells"
    match_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("matches.provider_id"), primary_key=True)
    player_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("players.provider_id"), primary_key=True)
    zone_row: Mapped[int] = mapped_column(Integer, primary_key=True)
    zone_col: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("teams.provider_id"))
    match_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    touch_count: Mapped[int] = mapped_column(Integer)


class InjuryModel(Base):
    __tablename__ = "injuries"
    player_provider_id: Mapped[str] = mapped_column(String(100), ForeignKey("players.provider_id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(50))
    detail: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TeamPerformanceSnapshotModel(Base):
    __tablename__ = "team_performance_snapshot"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league_code: Mapped[str] = mapped_column(String(20), index=True)
    season_year: Mapped[int] = mapped_column(Integer, index=True)
    team_name: Mapped[str] = mapped_column(String(255), index=True)
    matches_played: Mapped[int] = mapped_column(Integer)
    wins: Mapped[int] = mapped_column(Integer)
    draws: Mapped[int] = mapped_column(Integer)
    losses: Mapped[int] = mapped_column(Integer)
    goals_for: Mapped[int] = mapped_column(Integer)
    goals_against: Mapped[int] = mapped_column(Integer)
    points: Mapped[int] = mapped_column(Integer)
    form_points_last_5: Mapped[int] = mapped_column(Integer)
    home_points: Mapped[int] = mapped_column(Integer)
    away_points: Mapped[int] = mapped_column(Integer)
    expected_goals_avg: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PlayerConsistencySnapshotModel(Base):
    __tablename__ = "player_consistency_snapshot"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league_code: Mapped[str] = mapped_column(String(20), index=True)
    season_year: Mapped[int] = mapped_column(Integer, index=True)
    team_name: Mapped[str] = mapped_column(String(255), index=True)
    player_name: Mapped[str] = mapped_column(String(255), index=True)
    position: Mapped[str] = mapped_column(String(20))
    matches_played: Mapped[int] = mapped_column(Integer)
    minutes_played: Mapped[int] = mapped_column(Integer)
    goals: Mapped[int] = mapped_column(Integer)
    assists: Mapped[int] = mapped_column(Integer)
    average_rating: Mapped[float] = mapped_column(Float)
    rating_stddev: Mapped[float] = mapped_column(Float)
    consistency_score: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RefreshAuditModel(Base):
    __tablename__ = "refresh_audit"
    run_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    provider: Mapped[str] = mapped_column(String(50))
    league_code: Mapped[str] = mapped_column(String(20), index=True)
    season_year: Mapped[int] = mapped_column(Integer, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50))
    records_ingested: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
