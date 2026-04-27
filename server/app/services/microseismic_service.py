import math
import sys
from pathlib import Path
from typing import Any

try:
    import xlrd
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[3]
    local_deps = repo_root / ".tmp_pydeps"
    if local_deps.exists():
        sys.path.insert(0, str(local_deps))
    import xlrd

from app.services.centerline_service import LineFit, centerline_service


class MicroseismicService:
    def build_warning_data(self, file_contents: bytes, filename: str) -> dict[str, Any]:
        events = self._read_events(file_contents)
        if len(events) < 1:
            raise ValueError("No valid microseismic events found")

        event_points = [(event["x"], event["y"]) for event in events]
        centerline_payload = centerline_service.local_payload(event_points)
        line_data = centerline_payload["centerline"]
        line = LineFit(
            cx=line_data["point"][0],
            cy=line_data["point"][1],
            dx=line_data["direction"][0],
            dy=line_data["direction"][1],
        )

        q_r100_star = self._q_r100_star()
        for event in events:
            r = max(centerline_service.distance_to_line(event["x"], event["y"], line), 1.0)
            q_event_r100 = self._q_event_r100(event["energy_j"], r)
            w = q_event_r100 / q_r100_star
            event["r"] = r
            event["q_event_r100"] = q_event_r100
            event["w"] = w
            event["risk_level"] = self._risk_level(w)

        return {
            "meta": {
                **centerline_payload["meta"],
                "events_source": filename,
                "event_count": len(events),
                "warning_params": self._warning_params(),
                "q_r100_star": q_r100_star,
            },
            "centerline": centerline_payload["centerline"],
            "events": events,
        }

    def _read_events(self, file_contents: bytes) -> list[dict[str, Any]]:
        workbook = xlrd.open_workbook(file_contents=file_contents, on_demand=True)
        sheet = workbook.sheet_by_index(0)
        events: list[dict[str, Any]] = []
        for row in range(1, sheet.nrows):
            x = self._number(sheet.cell_value(row, 2))
            y = self._number(sheet.cell_value(row, 3))
            z = self._number(sheet.cell_value(row, 4))
            energy = self._number(sheet.cell_value(row, 5))
            old_w = self._number(sheet.cell_value(row, 6))
            if x is None or y is None or energy is None:
                continue
            events.append({
                "event_id": row,
                "date": self._text(sheet.cell_value(row, 0)),
                "time": self._text(sheet.cell_value(row, 1)),
                "x": x,
                "y": y,
                "z": z,
                "energy_j": energy,
                "old_w": old_w,
                "note": self._text(sheet.cell_value(row, 9)) if sheet.ncols > 9 else "",
            })
        return events

    def _q_event_r100(self, energy_j: float, r: float) -> float:
        a_mc = self._warning_params()["a_mc"]
        return energy_j * math.pow(10.0, (200.0 * a_mc - 100.0 * a_mc * math.log10(r)) / 57.0)

    def _q_r100_star(self) -> float:
        params = self._warning_params()
        sigma = 5400.0
        e_modulus = 2580000.0
        xi = 0.28
        lambda1 = 1496400.0
        lambda2 = 16000.0
        ps = 400.0
        p0 = 2.37
        phi1 = 0.5236
        phi2 = 0.34

        q = self._sanjiao(phi2)
        m = self._sanjiao(phi1)
        alpha = self._alpha(sigma, lambda1, lambda2, e_modulus, xi)
        beta = self._beta(sigma, lambda1, lambda2, e_modulus, xi)
        pfcr = p0 * math.sqrt((ps * (q - 1.0) + alpha) / beta)
        pfcr_upper = self._pfcr_upper(ps, pfcr, p0, q, alpha, beta)

        term1 = (m + 1.0) / 2.0
        term2 = pfcr_upper / sigma + (1.0 + lambda1 / e_modulus) / (m - 1.0)
        base = 1.0 + (1.0 - xi) * e_modulus / lambda1
        pcr_upper = sigma * (
            term1 * term2 * math.pow(base, (m - 1.0) / 2.0)
            - (lambda1 / e_modulus) / 2.0 * math.pow(base, (m + 1.0) / 2.0)
            - (1.0 + lambda1 / e_modulus) / (m - 1.0)
        )
        pmcr = params["section_factor"] * (2.0 * pcr_upper - (2.0 * pcr_upper - sigma) / (m + 1.0))
        sigma_bmax = params["omega"] * (pmcr - params["p0_input_kpa"])
        v_max = math.sqrt(sigma_bmax / (2.0 * params["rho_c"]))
        exponent = (100.0 * params["a_mc"]) / 57.0
        inner = math.pow(10.0, 2.05 + 57.0 * params["b_mc"] / (100.0 * params["a_mc"])) * v_max
        q_r100_initial = math.pow(inner, exponent)
        return min(params["q_min_r100"], q_r100_initial)

    def _warning_params(self) -> dict[str, float]:
        return {
            "p0_input_kpa": 39940.0,
            "omega": 0.85,
            "rho_c": 1350.0,
            "a_mc": 1.9,
            "b_mc": 1.9,
            "q_min_r100": 2.21e8,
            "section_factor": 0.89,
        }

    def _sanjiao(self, phi: float) -> float:
        return (1.0 + math.sin(phi)) / (1.0 - math.sin(phi))

    def _alpha(self, sigma: float, lambda1: float, lambda2: float, e_modulus: float, xi: float) -> float:
        return sigma * (lambda2 / e_modulus + lambda2 * (1.0 - xi) / lambda1 + xi)

    def _beta(self, sigma: float, lambda1: float, lambda2: float, e_modulus: float, xi: float) -> float:
        return sigma * (lambda2 / e_modulus + lambda2 * (1.0 - xi) / lambda1)

    def _pfcr_upper(self, ps: float, pfcr: float, p0: float, q: float, alpha: float, beta: float) -> float:
        ratio = pfcr / p0
        return (
            ps * math.pow(ratio, q - 1.0)
            + (alpha / (1.0 - q)) * (1.0 - math.pow(ratio, q - 1.0))
            + (beta / (1.0 + q)) * (1.0 - math.pow(ratio, q + 1.0))
        )

    def _risk_level(self, w: float) -> str:
        if w < 0.25:
            return "无"
        if w < 0.5:
            return "弱"
        if w < 0.75:
            return "中"
        return "强"

    def _number(self, value: Any) -> float | None:
        try:
            if value == "":
                return None
            number = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(number):
            return None
        return number

    def _text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)


microseismic_service = MicroseismicService()
