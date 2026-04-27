import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_X_OFFSET = 379000.0
PROJECT_Y_OFFSET = 4345700.0
LOCAL_FIT_PADDING = 1000.0


@dataclass(frozen=True)
class LineFit:
    cx: float
    cy: float
    dx: float
    dy: float


class CenterlineService:
    def __init__(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[3]
        self.database_file = self.repo_root / "database" / "centerline_points.csv"
        self.points: list[tuple[float, float]] = []
        self.line: LineFit | None = None
        self.segment: list[list[float]] = []
        self.reload()

    def reload(self) -> None:
        self.points = self._read_points()
        if len(self.points) < 2:
            raise ValueError("Not enough centerline points")
        self.line = self._fit_line(self.points)
        self.segment = self._line_segment(self.line, self.points)

    def payload(self) -> dict[str, Any]:
        line = self._require_line()
        return self._payload_for(line, self.segment, len(self.points), self._bounds(self.segment))

    def local_payload(self, reference_points: list[tuple[float, float]]) -> dict[str, Any]:
        fit_points = self._select_local_points(reference_points)
        line = self._fit_line(fit_points)
        segment = self._line_segment(line, fit_points)
        bounds = self._bounds(reference_points + segment)
        return self._payload_for(line, segment, len(fit_points), bounds)

    def _payload_for(
        self,
        line: LineFit,
        segment: list[list[float]],
        fit_points: int,
        bounds: dict[str, float],
    ) -> dict[str, Any]:
        return {
            "meta": {
                "centerline_source": str(self.database_file),
                "centerline_points": len(self.points),
                "fit_points": fit_points,
                "coordinate_offset": {"x": PROJECT_X_OFFSET, "y": PROJECT_Y_OFFSET},
                "bounds": bounds,
            },
            "centerline": {
                "point": [line.cx, line.cy],
                "direction": [line.dx, line.dy],
                "segment": segment,
            },
            "events": [],
        }

    def distance(self, x: float, y: float) -> float:
        line = self._require_line()
        return self.distance_to_line(x, y, line)

    def distance_to_line(self, x: float, y: float, line: LineFit) -> float:
        return abs((x - line.cx) * (-line.dy) + (y - line.cy) * line.dx)

    def combined_bounds(self, points: list[tuple[float, float] | list[float]]) -> dict[str, float]:
        return self._bounds(points + self.segment)

    def _select_local_points(self, reference_points: list[tuple[float, float]]) -> list[tuple[float, float]]:
        if not reference_points:
            return self.points

        xs = [point[0] for point in reference_points]
        ys = [point[1] for point in reference_points]
        xmin = min(xs) - LOCAL_FIT_PADDING
        xmax = max(xs) + LOCAL_FIT_PADDING
        ymin = min(ys) - LOCAL_FIT_PADDING
        ymax = max(ys) + LOCAL_FIT_PADDING
        selected = [
            (x, y)
            for x, y in self.points
            if xmin <= x <= xmax and ymin <= y <= ymax
        ]
        return selected if len(selected) >= 2 else self.points

    def _require_line(self) -> LineFit:
        if self.line is None:
            raise ValueError("Centerline has not been fitted")
        return self.line

    def _read_points(self) -> list[tuple[float, float]]:
        if not self.database_file.exists():
            raise FileNotFoundError(self.database_file)

        points: list[tuple[float, float]] = []
        with self.database_file.open("r", encoding="utf-8", newline="") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                x = self._number(row.get("local_x") or row.get("x"))
                y = self._number(row.get("local_y") or row.get("y"))
                if x is None or y is None:
                    continue
                points.append((x, y))
        return points

    def _fit_line(self, points: list[tuple[float, float]]) -> LineFit:
        cx = sum(x for x, _ in points) / len(points)
        cy = sum(y for _, y in points) / len(points)
        sxx = sum((x - cx) * (x - cx) for x, _ in points)
        syy = sum((y - cy) * (y - cy) for _, y in points)
        sxy = sum((x - cx) * (y - cy) for x, y in points)
        angle = 0.5 * math.atan2(2.0 * sxy, sxx - syy)
        dx = math.cos(angle)
        dy = math.sin(angle)
        if dx < 0:
            dx = -dx
            dy = -dy
        return LineFit(cx=cx, cy=cy, dx=dx, dy=dy)

    def _line_segment(self, line: LineFit, points: list[tuple[float, float]]) -> list[list[float]]:
        projections = [(x - line.cx) * line.dx + (y - line.cy) * line.dy for x, y in points]
        start = min(projections)
        end = max(projections)
        return [
            [line.cx + start * line.dx, line.cy + start * line.dy],
            [line.cx + end * line.dx, line.cy + end * line.dy],
        ]

    def _bounds(self, points: list[tuple[float, float] | list[float]]) -> dict[str, float]:
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
        pad_x = max((max(xs) - min(xs)) * 0.08, 20.0)
        pad_y = max((max(ys) - min(ys)) * 0.08, 20.0)
        return {
            "xmin": min(xs) - pad_x,
            "xmax": max(xs) + pad_x,
            "ymin": min(ys) - pad_y,
            "ymax": max(ys) + pad_y,
        }

    def _number(self, value: Any) -> float | None:
        try:
            if value in (None, ""):
                return None
            number = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(number):
            return None
        return number


centerline_service = CenterlineService()
